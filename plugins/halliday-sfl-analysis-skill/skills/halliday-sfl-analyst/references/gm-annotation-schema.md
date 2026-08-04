# Grammatical-metaphor annotation contract: Schema v3

Schema v3 is for **annotate** mode and for research tasks that produce formal
item-level coding. A research method, source-audit, statistical, or publication
report does not require JSON. Explain mode uses the compact reasoning sequence in
[gm-decision-protocol.md](gm-decision-protocol.md).

Machine contract:
[gm-annotation-v3.schema.json](gm-annotation-v3.schema.json).

## Contents

1. [Design goals](#1-design-goals)
2. [Core record](#2-core-record)
3. [Decision invariants](#3-decision-invariants)
4. [Framework profiles](#4-framework-profiles)
5. [Validation and exchange formats](#5-validation-commands)
6. [V2 compatibility](#7-v2-compatibility)
7. [Research coding](#8-research-mode-coding-requirements)

## 1. Design goals

V3 keeps the cross-stratal decision explicit while reducing the mandatory v2
diagnostic surface. It supports:

- one JSON object;
- a JSON array;
- JSONL/NDJSON, one object per non-empty line;
- CSV, with arrays and nested objects encoded as JSON cells;
- legacy v2 validation through the same validator.

The schema does not perform automatic linguistic analysis. It records the evidence
and decision produced by a human, rule baseline, LLM, or hybrid process.

## 2. Core record

Every v3 record contains:

```json
{
  "schema_version": "3.0",
  "analysis_mode": "annotate",
  "document_id": "doc-001",
  "sentence_id": "s-001",
  "sentence": "人口的迅速增长带来了资源压力。",
  "context_before": "",
  "context_after": "",
  "language": "zh",
  "unit_type": "PHRASE",
  "candidate_span": "人口的迅速增长",
  "span_start": 0,
  "span_end": 7,
  "semantic_category": "PROCESS",
  "actual_realization": "process meaning realized as a nominal group",
  "congruent_realization": "人口迅速增长",
  "congruent_agnate": "人口迅速增长，因而带来了资源压力。",
  "remapping_type": "PROCESS_TO_THING",
  "candidate_rule": "PROCESS_NOMINAL_GROUP",
  "mapping_mismatch": true,
  "congruent_agnate_plausible": true,
  "remapping_explicit": true,
  "lexical_only": false,
  "gm_candidate": true,
  "ideational_gm_status": "TYPICAL_GM",
  "interpersonal_gm_status": "NON_GM",
  "polarity_metaphor": false,
  "positive_evidence": ["增长 retains process meaning and heads a nominal group"],
  "counter_evidence": ["Chinese has no obligatory derivational nominalizer"],
  "context_sufficiency": "SUFFICIENT",
  "confidence": "HIGH",
  "needs_human_review": true,
  "framework_profile": "HALLIDAY_PLUS_YANG_OPERATIONAL",
  "operational_tests": ["RE_MAPPING", "CONGRUENT_AGNATE", "MPP", "FRP"],
  "analyzer_version": "halliday-sfl-analyst/1.4.0",
  "annotator_type": "HUMAN",
  "source_provenance": "constructed:gm-gold-v3",
  "candidate_interpretations": [],
  "rank_relation": "CLAUSE_TO_GROUP",
  "realization_degree": "FULL",
  "semantic_junction": "PROCESS_ENTITY",
  "exclusion_reason": "NONE"
}
```

Offsets are zero-based Unicode code-point offsets with an exclusive `span_end`:

```text
sentence[span_start:span_end] == candidate_span
```

They are not UTF-8 byte offsets.

## 3. Decision invariants

The validator enforces:

```text
gm_candidate =
    mapping_mismatch
    AND congruent_agnate_plausible
    AND remapping_explicit
    AND NOT lexical_only
```

It also enforces:

- `INSUFFICIENT` context → both axes `INDETERMINATE`, `LOW`, review required,
  and `gm_candidate=false`;
- conditional readings under insufficient context appear only in
  `candidate_interpretations`;
- `TYPICAL_GM` requires `gm_candidate=true` and a plausible agnate;
- without a plausible agnate, the maximum positive label is `MARGINAL_GM`;
- lexical metaphor alone cannot receive a GM label;
- formal records contain positive evidence, counterevidence, and applied tests;
- uncertain, marginal, and indeterminate records require review;
- a private absolute filesystem path is not valid provenance.

The Python validator mirrors critical constraints in the JSON Schema so records are
safe even when a caller does not use an external JSON-Schema library.

## 4. Framework profiles

- `HALLIDAY_CORE`: the decision is grounded in semantic–lexicogrammatical
  re-mapping and a congruent agnate.
- `HALLIDAY_PLUS_YANG_OPERATIONAL`: the Hallidayan decision is supplemented, where
  relevant, by semantic junction, MPP, and rank diagnostics from Wen Li and Bingjun
  Yang (2024); FRP from Bingjun Yang (2020); Context-first/AS IF from Bingjun Yang
  (2019); or polarity tests from Bingjun Yang and Hongmiao Gao (2023). The profile
  name does not refer to Yang Yanning's Chinese descriptive framework.
- `CUSTOM`: the record must state its tests and source lineage; custom tools cannot
  replace the core mapping evidence.

Use the extended profile only when its type-specific tests apply. An optional `mpp`
object preserves candidate agnates, selection level, pass/fail, higher-priority
alternatives, and cross-linguistic caution. A `PASS` validates the agnate relation
only; it is not a GM verdict.

## 5. Validation commands

Validate every formal record before returning, saving, or sharing it, including a
single record intended for inline output. Validation proves contract consistency, not
linguistic truth.

From the repository root:

```bash
python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/validate_gm_annotation.py annotation.json
python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/validate_gm_annotation.py annotations.jsonl
python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/validate_gm_annotation.py annotations.csv
```

Force a container or schema only when needed:

```bash
python3 .../validate_gm_annotation.py --format jsonl --schema-version 3 data.txt
```

Exit status is `0` for valid data, `1` for annotation errors, and `2` for unreadable
input/schema/rule configuration.

## 6. JSONL and CSV rules

JSONL uses UTF-8; each non-empty line must be one object. Arrays inside a JSONL line
are rejected. An empty file is invalid.

CSV is parsed as data only: no formula or expression is evaluated. It must have
unique, non-empty headers. Booleans are exactly `true` or `false`; integers are
decimal; arrays and `mpp` are JSON-encoded cells. Example cell values:

```text
["RE_MAPPING","CONGRUENT_AGNATE"]
{"applicability":"NOT_APPLICABLE", ...}
```

For lossless exchange, prefer JSONL. CSV is intended for review tools and spreadsheet
round-trips.

## 7. V2 compatibility

The bundled [gm-annotation-v2.schema.json](gm-annotation-v2.schema.json) remains a
legacy contract. The validator routes `schema_version="3.0"` to v3 and an
unversioned v2-shaped record (or explicit `schema_version="2.0"`) to v2. The
conservative context gate applies to both versions.

New projects should write v3. Do not silently transform v2 data during validation;
preserve the original record and migrate it in a reviewed step because several v2
diagnostics collapse into v3 evidence/test fields.

## 8. Research-mode coding requirements

When research produces formal item-level coding for a corpus or evaluation:

1. retain complete `context_before` and `context_after` according to a documented
   window or discourse-unit rule;
2. use stable document/sentence IDs and provenance that does not expose private
   paths;
3. record analyzer and ruleset versions;
4. report each label with a denominator;
5. report the count and proportion requiring human review;
6. inspect all indeterminate cases or a reproducible stratified review sample;
7. keep candidate extraction recall separate from final GM precision/recall.

The compact gold fixture in `tests/fixtures/gm-gold-v3.json` contains only original
or constructed examples and is expanded into Schema v3 records by the regression
tests. It is not a claim about natural-language frequency.
