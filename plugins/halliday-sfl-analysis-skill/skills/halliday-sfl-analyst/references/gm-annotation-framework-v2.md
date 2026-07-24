# Grammatical-metaphor annotation framework v2

Use this reference for item-by-item grammatical-metaphor (GM) annotation, JSON output, batch coding, gold-data preparation, or any request that asks whether a clause, phrase, word, or morpheme is GM. It turns the explanatory procedure in [gm-identification-protocol.md](gm-identification-protocol.md) into an auditable annotation contract.

## Contents

1. Scope and evidence status
2. Independent annotation axes
3. Context and congruent-agnate gates
4. Ideational and MPP workflow
5. Interpersonal workflow
6. Polarity workflow
7. Exclusions, confidence, and review
8. Output and validation contract
9. Adjudication rules
10. Theory lineage

## 1. Scope and evidence status

Distinguish:

- ideational GM (IGM);
- interpersonal GM (IPGM), including mood and modality metaphor;
- polarity metaphor, which may co-occur with either axis;
- non-GM, marginal, and indeterminate cases.

Do not infer GM from novelty, brevity, nominal form, a suffix, a proper name, an abbreviation, a technical term, lexical metaphor, embedding, or rank shift alone.

This operational contract is distilled from the user-supplied *Codex SFL GM Annotation Framework v2 (MPP)*. Treat the framework as an annotation policy, not as a publication by Halliday or Yang. Attribute its underlying theoretical tests to the sources in Section 10.

## 2. Independent annotation axes

Annotate ideational and interpersonal status independently:

```text
NON_GM | MARGINAL_GM | TYPICAL_GM | INDETERMINATE
```

An item may be typical on one axis and non-GM or indeterminate on the other. Record polarity separately. Never collapse the three decisions into one undifferentiated `GM` label.

Use the machine-readable contract in [gm-annotation-v2.schema.json](gm-annotation-v2.schema.json). Preserve every required key, including explicit `NONE`, `UNCLEAR`, `false`, empty arrays, and `null` values; do not silently omit fields that do not apply.

## 3. Context and congruent-agnate gates

### Context gate

Set:

- `SUFFICIENT` when the unit, co-text, participant roles, and discourse function support the relevant decision;
- `PARTIAL` when a plausible decision is possible but an important ambiguity remains;
- `INSUFFICIENT` when the item is isolated or materially polysemous.

An isolated word is normally `INDETERMINATE` for interpersonal GM. Give conditional ideational readings instead of inventing a clause.

### Congruent-agnate gate

Construct the most natural, minimally changed wording that realizes the relevant contextual meaning more directly. Preserve participants, polarity, modal force, and logical relation where they are decisive.

Reject an agnate that:

- changes the proposition or proposal;
- is an unnatural dictionary definition;
- relies on a remote synonym when a direct formal relation exists;
- is reverse-engineered only to force a GM verdict.

If no stable agnate can be recovered, use `INDETERMINATE` when ambiguity is unresolved and `NON_GM` when the proposed GM relation has no defensible basis.

## 4. Ideational and MPP workflow

Apply the steps in this order.

### Step 1: recover and enumerate

1. Recover the congruent agnate.
2. State source semantic category and rank.
3. State target grammatical category and rank.
4. For a nominalizing candidate, enumerate all serious agnate pairings before choosing one.

### Step 2: apply Morphological Priority Principle

MPP is a mandatory **agnate-selection gate for nominalizing metaphor**, not a universal proof of IGM and not a requirement for every non-nominal IGM.

For English, use this strict order:

1. `DERIVATIONAL_AGNATION`: a direct derivative such as `develop → development`;
2. `ING_TO_AGNATION`: `-ing` or infinitival agnation only where no suitable direct derivative exists;
3. `NON_MORPHOLOGICAL_AGNATION`: semantic agnation such as `if → condition` only where neither higher option is available.

If a higher-priority legitimate relation exists but the annotation selects a lower-priority form or arbitrary synonym, set:

```text
mpp_status = FAIL
mpp_higher_priority_available = true
```

Explain the violation. An `MPP_FAIL` item cannot be `TYPICAL_GM` on the ideational axis. Re-select the legitimate agnate when possible; otherwise use a non-typical verdict.

`MPP_PASS` establishes only that the chosen agnate relation is legitimate. It does not establish rank shift, full realization, semantic junction, or GM by itself.

### Step 3: adapt MPP cautiously for Chinese

Do not fabricate English-style derivation. Use:

1. `ZH_SAME_CORE_MORPHEME`;
2. `ZH_OVERT_NOMINALIZING_RESOURCE`;
3. `ZH_MINIMAL_STRUCTURAL_AGNATION`;
4. `ZH_NON_MORPHOLOGICAL_AGNATION`.

Resources such as `性、度、率、量、感、力、化、行为、过程、现象` are evidence to test, not automatic nominalizers. Prefer the Chinese agnate that retains the most core morphemes and makes the smallest defensible structural change.

For every Chinese item to which MPP applies, set:

```text
mpp_crosslinguistic_caution = true
needs_human_review = true
```

Use `UNCLEAR` when Chinese formal agnation cannot be stably ordered. MPP selects the comparison; it does not replace the rank, realization, junction, or exclusion tests.

### Step 4: test rank, realization, and semantic junction

Record the downward rank relation, if any:

```text
CLAUSE_COMPLEX_TO_CLAUSE
CLAUSE_COMPLEX_TO_GROUP
CLAUSE_COMPLEX_TO_WORD
CLAUSE_TO_GROUP
CLAUSE_TO_WORD
GROUP_TO_WORD
OTHER
```

Assess Full Realization Principle:

- `FULL`: meaning and form are both compressed;
- `INTERMEDIATE`: only partial compression;
- `RAW`: semantic packaging occurs while finite or clearly clausal form remains.

Then test semantic junction. A nominalized process, quality, circumstance, relator, or polarity must retain its source meaning while gaining entity-like affordances. A noun that denotes only an agent, patient, product, tool, place, or measure lacks the required junction.

### Step 5: assign ideational status

Assign `TYPICAL_GM` to a nominalizing candidate only when all are true:

- a contextual congruent agnate is recoverable;
- `mpp_status = PASS`;
- a downward rank shift is present;
- `frp_realization = FULL`;
- a semantic junction is present;
- `exclusion_reason = NONE`.

Use `MARGINAL_GM` for defensible partial realization or gradient re-mapping. Use `NON_GM` for a failed positive relation or a valid exclusion. Use `INDETERMINATE` when missing context or unresolved agnation prevents a decision.

## 5. Interpersonal workflow

Start with context, never surface Mood.

1. Infer `speech_function`: giving or demanding information or goods-and-services.
2. Identify `mood_form`.
3. Establish the contextually congruent realization.
4. Apply the AS IF test: is this form functioning as if it realized a different speech-function value?
5. Record the mismatch, agnate, response potential, and meaning consequence.

Typical baselines are statement–declarative, question–interrogative, command–imperative, and a contextually conventional modal interrogative or declarative for an offer. An interrogative offer is therefore not automatically a mood metaphor.

For mood metaphor, use paths such as:

```text
COMMAND_AS_DECLARATIVE
COMMAND_AS_INTERROGATIVE
STATEMENT_AS_INTERROGATIVE
QUESTION_AS_DECLARATIVE
OFFER_AS_INTERROGATIVE
```

For modality metaphor, first determine `PROBABILITY`, `USUALITY`, `OBLIGATION`, or `INCLINATION`, then record subjective/objective orientation and explicit/implicit realization. A projecting clause such as `I think` or `我觉得` must be interpreted from its discourse force; it may realize probability in one context and attenuated obligation in another.

Without a clause and enough exchange context, set interpersonal status to `INDETERMINATE`.

## 6. Polarity workflow

Record polarity separately from the two main axes.

For ideational polarity, test whether negative meaning is reconstrued as:

- `PARTICIPATION`;
- `PROCESSATION`;
- `QUALIFICATION`;
- `CIRCUMSTANTIATION`.

Require a direct negative agnate, category or rank evidence, semantic junction, and a counter-test against ordinary lexicalized negation.

For interpersonal polarity, test Mood tension, modality projection, or negative transfer. In `I don't think he is coming`, compare the projecting-clause negative with the more direct `I think he isn't coming`, and record the location of the negative in the evidence even though the compact schema stores the subtype.

An item may carry ideational GM, interpersonal GM, and polarity metaphor simultaneously.

## 7. Exclusions, confidence, and review

Use one explicit exclusion when it provides the decisive non-GM account:

```text
PROPER_NAME
ABBREVIATION_ONLY
ORDINARY_COMPOUND
LEXICAL_METAPHOR_ONLY
TECHNICALIZED_OR_DEAD
EVENT_NOUN_WITHOUT_AGNATE
PARTICIPANT_NOUN_ONLY
RAW_EMBEDDING
NO_SEMANTIC_JUNCTION
NO_CONTEXT
OTHER
```

Treat technicalization and lexicalization as gradient; do not use `TECHNICALIZED_OR_DEAD` from intuition alone.

Set confidence:

- `HIGH`: full context, recoverable agnate, mapping, type-specific tests, and exclusion checks;
- `MEDIUM`: main relation is defensible but polysemy, lexicalization, or context remains partial;
- `LOW`: evidence rests mainly on form, a dictionary gloss, or speculation.

A low-confidence result cannot be an unqualified `TYPICAL_GM`. Set `needs_human_review = true` whenever confidence is not high, either main status is marginal or indeterminate, MPP is unclear, or Chinese MPP adaptation applies.

Populate both `evidence` and `counterevidence`. A label without the strongest contrary analysis is incomplete.

## 8. Output and validation contract

For every annotated item:

1. Output one JSON object conforming to [gm-annotation-v2.schema.json](gm-annotation-v2.schema.json).
2. Follow it with a Chinese explanation of no more than 120 Chinese characters. If the user explicitly requests another language, use one equivalently concise sentence.
3. Order the explanation: agnate and candidates → MPP choice → rank/category change → FRP or Context-first/AS IF → exclusion → verdict and confidence.
4. After all items, add complete page-verified theoretical sources under the normal citation protocol. Source entries are outside the item JSON and do not count toward the 120-character explanation.

For saved or batch annotations, run:

```bash
python3 scripts/validate_gm_annotation.py annotation.json
```

The validator checks field presence, data types, enums, MPP priority consistency, typical-GM gates, Chinese review flags, evidence/counterevidence, and review requirements. A schema-valid record can still be analytically wrong; validation guarantees contract consistency, not theoretical truth.

## 9. Adjudication rules

When two analyses disagree, compare them in this order:

1. contextual meaning and speech function;
2. naturalness and semantic fidelity of the congruent agnate;
3. MPP candidate enumeration and priority;
4. rank relation and realization degree;
5. semantic junction or AS IF evidence;
6. exclusion and counter-analysis;
7. source lineage and verified locator.

Retain both candidate analyses when the dispute cannot be resolved. Mark `INDETERMINATE` or `MARGINAL_GM`, identify the decision-changing missing evidence, and require human review. Do not resolve disagreement by majority intuition alone.

## 10. Theory lineage

- Halliday, M. A. K., and Christian M. I. M. Matthiessen. 2014. *Halliday's Introduction to Functional Grammar*, 4th ed., Sections 10.5.2 and 10.5.4 (printed pp. 712, 719; PDF pp. 731, 738): semantic–lexicogrammatical re-mapping and ideational GM.
- Li, Wen, and Bingjun Yang. 2024. `Towards a system of principles for identifying nominalizing metaphors`. *Lingua* 312: 103832, Sections 4–6 (printed pp. 10–18; PDF pp. 10–18): semantic junction, morphological priority, full realization, and rank shift.
- Yang, Bingjun. 2020. `Full realization principle for the identification of ideational grammatical metaphor: nominalization as example`. *Journal of World Languages* 6(3): 161–174 (printed pp. 166–170; PDF pp. 6–10): full, intermediate, and raw realization.
- Yang, Bingjun. 2019. `Interpersonal metaphor revisited: identification, categorization, and syndrome`. *Social Semiotics* 29(2): 186–203 (printed pp. 193–199; PDF pp. 9–15): Context-first and AS IF principles.
- Yang, Bingjun, and Hongmiao Gao. 2023. `Polarity metaphor in English: Definition, identification, and categorization`. *Lingua* 295: 103623 (printed pp. 6–13; PDF pp. 6–13): ideational and interpersonal polarity metaphor.

Re-open the complete source page before citing any of these claims in a user answer.
