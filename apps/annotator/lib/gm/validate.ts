import schemaJson from "./schema-v3.json";
import rules from "./candidate-rules.json";

// A deliberately bounded evaluator for the exact JSON Schema vocabulary used by
// the public v3 contract. Unlike Ajv runtime compilation, this uses no eval/new
// Function and therefore also runs in Cloudflare Workers. Ajv parity is tested.
type Spec = {
  $ref?: string; type?: string | string[]; const?: unknown; enum?: unknown[];
  minLength?: number; minimum?: number; minItems?: number; items?: Spec;
  required?: string[]; properties?: Record<string, Spec>; additionalProperties?: boolean;
  not?: Spec; allOf?: Spec[]; if?: Spec; then?: Spec; else?: Spec;
};
const schema = schemaJson as unknown as Spec & { $defs: Record<string, Spec> };
export const GM_SCHEMA = schemaJson;
export const CANDIDATE_RULES = rules.rules.map(rule => rule.id);
const nominalizations = ["PROCESS_TO_THING", "FIGURE_TO_NOMINAL_GROUP", "QUALITY_TO_THING", "CIRCUMSTANCE_TO_THING", "LOGICAL_RELATION_TO_THING"];
export const isObject = (value: unknown): value is Record<string, unknown> => !!value && typeof value === "object" && !Array.isArray(value);
const substantive = (value: unknown): value is string => typeof value === "string" && !value.includes("\0") && /[\p{L}\p{N}]/u.test(value);
const lexical = (value: unknown) => typeof value === "string" ? value.toLocaleLowerCase().replace(/[^\p{L}\p{M}\p{N}]/gu, "") : "";
const same = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b);
function matchesType(value: unknown, type: string): boolean {
  switch (type) {
    case "object": return isObject(value);
    case "array": return Array.isArray(value);
    case "integer": return typeof value === "number" && Number.isSafeInteger(value);
    case "number": return typeof value === "number" && Number.isFinite(value);
    case "null": return value === null;
    case "boolean": return typeof value === "boolean";
    case "string": return typeof value === "string";
    default: throw new Error("Unsupported schema vocabulary");
  }
}
function shape(value: unknown, input: Spec, path: string, depth = 0): string[] {
  if (depth > 32) return [path + ": nesting limit exceeded"];
  let spec = input;
  if (spec.$ref) {
    const key = spec.$ref.replace("#/$defs/", "");
    if (!spec.$ref.startsWith("#/$defs/") || !schema.$defs[key]) throw new Error("Unsupported schema reference");
    spec = schema.$defs[key];
  }
  const errors: string[] = [];
  if (spec.type && !(Array.isArray(spec.type) ? spec.type : [spec.type]).some(type => matchesType(value, type))) return [path + ": incorrect type"];
  if ("const" in spec && !same(value, spec.const)) errors.push(path + ": invalid constant");
  if (spec.enum && !spec.enum.some(item => same(item, value))) errors.push(path + ": invalid enum");
  if (typeof value === "string" && Array.from(value).length < (spec.minLength ?? 0)) errors.push(path + ": string too short");
  if (typeof value === "number" && value < (spec.minimum ?? -Infinity)) errors.push(path + ": below minimum");
  if (Array.isArray(value)) {
    if (value.length < (spec.minItems ?? 0)) errors.push(path + ": too few items");
    if (spec.items) value.forEach((item, i) => errors.push(...shape(item, spec.items!, `${path}[${i}]`, depth + 1)));
  }
  if (isObject(value)) {
    for (const key of spec.required ?? []) if (!Object.hasOwn(value, key)) errors.push(`${path}.${key}: missing field`);
    for (const [key, item] of Object.entries(value)) {
      if (spec.properties?.[key]) errors.push(...shape(item, spec.properties[key], `${path}.${key}`, depth + 1));
      else if (spec.additionalProperties === false) errors.push(`${path}.${key}: unexpected field`);
    }
  }
  if (spec.not && shape(value, spec.not, path, depth + 1).length === 0) errors.push(path + ": forbidden value");
  for (const branch of spec.allOf ?? []) {
    const pass = !branch.if || shape(value, branch.if, path, depth + 1).length === 0;
    const consequent = pass ? (branch.if ? branch.then : branch) : branch.else;
    if (consequent) errors.push(...shape(value, consequent, path, depth + 1));
  }
  return errors;
}

/** Validates canonical v3 shape AND cross-field/offset/context invariants. */
export function validateRecord(value: unknown): string[] {
  const errors = shape(value, schema, "record");
  if (!isObject(value)) return errors;
  const r = value;
  const error = (message: string) => { errors.push("record: " + message); };
  for (const field of ["document_id", "sentence_id", "sentence", "candidate_span", "actual_realization", "candidate_rule", "analyzer_version", "source_provenance"]) {
    if (!substantive(r[field])) error(`${field} must contain linguistic content`);
  }
  if (typeof r.sentence === "string" && Number.isInteger(r.span_start) && Number.isInteger(r.span_end)) {
    const chars = Array.from(r.sentence);
    const start = r.span_start as number, end = r.span_end as number;
    if (start < 0 || start >= end || end > chars.length || chars.slice(start, end).join("") !== r.candidate_span) error("candidate_span must match sentence code-point offsets");
  }
  const formula = r.mapping_mismatch === true && r.congruent_agnate_plausible === true && r.remapping_explicit === true && r.lexical_only === false;
  if (r.gm_candidate !== formula) error("GM candidate must match all four mapping predicates");
  const statuses = [r.ideational_gm_status, r.interpersonal_gm_status];
  if (statuses.includes("TYPICAL_GM")) {
    if (!formula || r.confidence === "LOW" || r.exclusion_reason !== "NONE" || !substantive(r.congruent_agnate)) error("typical GM requires mapping, congruent agnate, adequate confidence and no exclusion");
  }
  for (const field of ["positive_evidence", "counter_evidence", "operational_tests"]) {
    if (!Array.isArray(r[field]) || !(r[field] as unknown[]).length || (r[field] as unknown[]).some(item => !substantive(item))) error(`${field} must contain substantive observations`);
  }
  const isolatedWord = r.unit_type === "WORD" && !!lexical(r.candidate_span) && lexical(r.sentence) === lexical(r.candidate_span) && !lexical(r.context_before) && !lexical(r.context_after);
  if (isolatedWord && r.context_sufficiency !== "INSUFFICIENT") error("isolated WORD requires insufficient context");
  if (r.context_sufficiency === "INSUFFICIENT" || isolatedWord) {
    const expected: Record<string, unknown> = {
      ideational_gm_status: "INDETERMINATE", interpersonal_gm_status: "INDETERMINATE", confidence: "LOW", needs_human_review: true,
      gm_candidate: false, semantic_category: "UNCLEAR", congruent_realization: null, congruent_agnate: null,
      remapping_type: "NONE", mapping_mismatch: false, congruent_agnate_plausible: false, remapping_explicit: false,
      lexical_only: false, rank_relation: "UNCLEAR", realization_degree: "UNCLEAR", semantic_junction: "UNCLEAR", exclusion_reason: "NO_CONTEXT"
    };
    for (const [key, expectedValue] of Object.entries(expected)) if (r[key] !== expectedValue) error(`insufficient context requires ${key}=${JSON.stringify(expectedValue)}`);
    if (!Array.isArray(r.candidate_interpretations) || !r.candidate_interpretations.length || r.candidate_interpretations.some(item => !substantive(item))) error("insufficient context requires conditional interpretations");
  }
  if (r.context_sufficiency === "PARTIAL" && (r.confidence === "HIGH" || r.needs_human_review !== true)) error("partial context must lower confidence and require review");
  if ((r.confidence !== "HIGH" || statuses.some(status => status === "MARGINAL_GM" || status === "INDETERMINATE")) && r.needs_human_review !== true) error("uncertain decisions require review");
  if (!CANDIDATE_RULES.includes(r.candidate_rule as typeof CANDIDATE_RULES[number])) error("unknown candidate_rule");
  if (typeof r.source_provenance === "string" && /(?:\/Users\/|\/home\/|[A-Za-z]:\\Users\\)/.test(r.source_provenance)) error("private absolute paths cannot be provenance");
  const mpp = isObject(r.mpp) ? r.mpp : undefined;
  if (r.ideational_gm_status === "TYPICAL_GM" && nominalizations.includes(String(r.remapping_type)) && r.framework_profile === "HALLIDAY_PLUS_YANG_OPERATIONAL") {
    if (["NONE", "UNCLEAR"].includes(String(r.rank_relation)) || r.realization_degree !== "FULL" || ["NONE", "UNCLEAR"].includes(String(r.semantic_junction)) || mpp?.status !== "PASS") error("extended typical nominalizing GM requires rank, FULL, junction and MPP PASS");
  }
  if (mpp) {
    const { applicability, status } = mpp;
    if (applicability === "APPLICABLE" && (!Array.isArray(mpp.candidate_agnates) || !mpp.candidate_agnates.length || !["PASS", "FAIL", "UNCLEAR"].includes(String(status)))) error("applicable MPP requires agnates and a result");
    if (applicability === "NOT_APPLICABLE" && (status !== "NOT_APPLICABLE" || mpp.agnation_level !== "NOT_APPLICABLE" || !Array.isArray(mpp.candidate_agnates) || mpp.candidate_agnates.length !== 0 || mpp.selected_agnate !== null)) error("non-applicable MPP must not select an agnate");
    if (applicability === "UNCLEAR" && status !== "UNCLEAR") error("unclear MPP requires unclear result");
    if (["PASS", "FAIL"].includes(String(status)) && applicability !== "APPLICABLE") error("MPP result requires applicable test");
    if (status === "PASS" && (!substantive(mpp.selected_agnate) || !Array.isArray(mpp.candidate_agnates) || !mpp.candidate_agnates.includes(mpp.selected_agnate) || mpp.higher_priority_available === true)) error("MPP PASS requires the closest listed agnate");
    if (status === "FAIL" && (!substantive(mpp.violation_reason) || (r.ideational_gm_status === "TYPICAL_GM" && nominalizations.includes(String(r.remapping_type))))) error("MPP FAIL requires a reason and excludes typical nominalizing GM");
    if (r.language === "zh" && applicability !== "NOT_APPLICABLE" && (mpp.crosslinguistic_caution !== true || r.needs_human_review !== true || (applicability === "APPLICABLE" && !String(mpp.agnation_level).startsWith("ZH_")))) error("Chinese MPP requires language-specific level, caution and review");
    if (r.language === "en" && applicability === "APPLICABLE" && String(mpp.agnation_level).startsWith("ZH_")) error("English MPP cannot use Chinese agnation levels");
  }
  if (r.polarity_metaphor === true ? (r.polarity_subtype ?? "NONE") === "NONE" : (r.polarity_subtype ?? "NONE") !== "NONE") error("polarity subtype must match polarity decision");
  return errors;
}
