# Grammatical-metaphor decision protocol

Use this protocol for any clause, phrase, word, morpheme, buzzword, or corpus span
that may involve grammatical metaphor (GM). The default product is an explanation,
not a JSON record. Formal records are governed by
[gm-annotation-schema.md](gm-annotation-schema.md).

## Contents

1. [Work mode](#1-select-the-work-mode-first)
2. [Context gate](#2-apply-the-context-gate-before-any-label)
3. [Contextual meaning and agnate](#3-establish-the-contextual-meaning)
4. [Mapping and type-specific tests](#5-make-both-mapping-layers-explicit)
5. [Counter-analysis and decision](#7-test-the-strongest-non-gm-analysis)
6. [Output, annotation, and lineage](#9-explain-mode-output)

## 1. Select the work mode first

- **explain** (default): answer the analytical question directly in prose or a small
  table. Do not emit full JSON unless the user asks for it.
- **annotate**: use Schema v3 when the user explicitly requests annotation, coding,
  JSON, Schema output, or batch labels. When formal item records are the primary
  deliverable, annotate takes priority over research. Validate every record before
  returning it, including a single inline record.
- **research**: use complete context, provenance, analyzer version, uncertainty
  counts, and a review sample for corpus, method, source-audit, evaluation, or
  publication work. Keep the report in prose or tables unless it also produces formal
  item-level coding; use Schema v3 and validate every record only for that coding.

Depth such as quick/full is secondary to mode. A full prose analysis remains
`explain`; a one-item JSON coding request is `annotate`.

## 2. Apply the context gate before any label

Classify context as:

- `SUFFICIENT`: the unit, co-text, participant roles, and discourse function support
  the relevant decision;
- `PARTIAL`: a leading analysis is possible but a material ambiguity remains;
- `INSUFFICIENT`: an isolated or materially polysemous unit cannot establish the
  contextual meaning or exchange.

The following invariant is non-negotiable:

```python
if context_sufficiency == "INSUFFICIENT":
    ideational_gm_status = "INDETERMINATE"
    interpersonal_gm_status = "INDETERMINATE"
    confidence = "LOW"
    needs_human_review = True
```

In Schema v3, `gm_candidate` must also be `false`. Conditional readings may be
preserved only in `candidate_interpretations` or explicitly conditional prose. Do not
convert an isolated suffix, noun, or interrogative into a high-confidence GM label.

## 3. Establish the contextual meaning

Before inspecting form, identify the value at issue:

- process, quality, Thing, circumstance, figure, sequence, or logical relation;
- statement, question, command, or offer;
- probability, usuality, obligation, or inclination;
- direct or displaced negative meaning.

Use surrounding clauses, genre, speaker roles, and actual or expected response. State
any assumption that could change the verdict.

## 4. Construct the congruent agnate

Give the most natural, minimally changed realization of the same relevant meaning.
Preserve participants, polarity, modal force, and logical relation where decisive.

Reject an agnate that is ungrammatical, changes the proposal, is merely a dictionary
definition, ignores a closer formal relation, or exists only to force a metaphor
analysis. If no reasonable agnate is available, the maximum positive verdict is
`MARGINAL_GM`; use `INDETERMINATE` when the relation itself is unresolved.

For an isolated word, give conditional readings, for example:

```text
development
- event reading: X developed Y → X's development of Y
- established field/entity reading: may be lexicalized, with no active re-mapping
```

The result remains `INSUFFICIENT / INDETERMINATE / LOW / review required` until a
real context selects a reading.

## 5. Make both mapping layers explicit

Record or explain:

```text
contextual semantic value → actual lexicogrammatical realization
same relevant value        → more congruent realization
```

Then identify the re-mapping. The core candidate formula is:

```text
gm_candidate =
    mapping_mismatch
    AND congruent_agnate_plausible
    AND remapping_explicit
    AND NOT lexical_only
```

Every predicate represents evidence, not a model score. If any predicate is unknown,
do not mark a typical GM. A candidate extractor may nominate a span, but only this
cross-layer decision can promote it.

## 6. Run the type-specific tests

### Ideational and nominalizing candidates

First decide whether the source meaning remains active while the wording gains
another category's affordances. Then, only when
`HALLIDAY_PLUS_YANG_OPERATIONAL` is selected, record:

1. semantic junction;
2. MPP agnate selection;
3. full/intermediate/raw realization;
4. rank relation;
5. exclusions and the strongest counter-analysis.

Semantic junction, MPP, and rank diagnostics here come from Wen Li and Bingjun Yang
(2024); FRP comes from Bingjun Yang (2020) and is incorporated into that later
profile. A downward rank movement is strong evidence, not a sufficient condition;
MPP selects an agnate and does not itself prove GM.

Exclude ordinary entity nouns, ordinary event clauses, product/agent/instrument
nouns without a junction, ordinary embedding, lexical metaphor alone, and a
lexicalized event noun whose process meaning is inactive in the current use.

### Interpersonal candidates

Under the applicable extended profile, use Bingjun Yang's (2019) Context-first and AS
IF tests:

1. infer whether the exchange gives/demands information or goods-and-services;
2. use response potential as evidence;
3. identify the contextually congruent Mood or modal realization;
4. compare it with the selected form;
5. explain negotiability, authority, distance, commitment, or politeness.

`Would you like some tea?` is ordinarily a congruent offer, not automatically a
metaphorical command. `Would you close the door?` can realize a command in an
appropriate exchange, with `Close the door` as a congruent agnate. The context, not
interrogative form alone, determines the analysis.

### Polarity candidates

Identify the negative meaning and give a direct negative agnate. Then show how the
negative is relocated or construed through participation, Process, quality,
circumstance, Mood, or modality. Negative vocabulary by itself is not polarity GM.

### Chinese candidates

Construct the agnate in natural Chinese. Analyze the whole verbal group, including
resultative and directional complements. Treat zero derivation, `的`, nominal-group
position, sentence-final particles, `是……的`, `有……`, and `我想/我认为/我觉得`
as clues only. Use [chinese-sfl-analysis.md](chinese-sfl-analysis.md) for the
language-specific branch.

## 7. Test the strongest non-GM analysis

Every positive or borderline decision must state the best alternative explanation:

- ordinary entity or event reference;
- lexical metaphor only;
- lexicalized/technicalized noun;
- ordinary embedding or rank shift;
- literal Mental/Relational Process;
- conventional offer/question rather than a Mood mismatch;
- insufficient or conflicting context.

Do not hide counterevidence. A high-confidence result needs a reason the strongest
alternative fails in this context.

## 8. Assign the two axes independently

Use:

```text
NON_GM | MARGINAL_GM | TYPICAL_GM | INDETERMINATE
```

Keep ideational and interpersonal status separate; record polarity in addition. Use
`MARGINAL_GM` as the formal borderline label. Set human review when confidence is
not high, either axis is marginal/indeterminate, the context is partial/insufficient,
or a cross-linguistic operational test remains uncertain.

## 9. Explain-mode output

For an ordinary GM instance question, use this compact order:

1. **Direct conclusion**: GM / borderline / not GM / insufficient context.
2. **Context used**: what reading or speech function is supported.
3. **More congruent agnate**: or explain why no stable one is available.
4. **Mapping**: semantic category → actual grammar versus congruent grammar.
5. **Re-mapping type and effect**: agency, time, causality, abstraction,
   negotiability, or commitment.
6. **Counter-analysis and confidence**.
7. **Verified theoretical sources** when theory is invoked.

Do not append a complete Schema record unless the user selected annotate or the
research task produces formal item-level coding.

## 10. Annotation and adjudication

For formal data, follow [gm-annotation-schema.md](gm-annotation-schema.md), run
`scripts/validate_gm_annotation.py`, and retain competing candidate interpretations
when adjudication cannot resolve them. Compare disagreements in this order: context,
agnate naturalness, explicit mapping, type-specific evidence, counter-analysis, then
source lineage. Validation proves contract consistency, not theoretical truth.

## 11. Theory lineage

The core re-mapping criterion is Hallidayan. Semantic junction, MPP, and rank as
operational diagnostics come from Wen Li and Bingjun Yang (2024); FRP and
Context-first/AS IF come from Bingjun Yang's later work. They are distinct from Yang
Yanning's Chinese descriptive framework. Use the complete source identities and
verified locators in [gm-theory.md](gm-theory.md), then reopen the supporting source
under [source-citation-protocol.md](source-citation-protocol.md) before citing it to
the user.
