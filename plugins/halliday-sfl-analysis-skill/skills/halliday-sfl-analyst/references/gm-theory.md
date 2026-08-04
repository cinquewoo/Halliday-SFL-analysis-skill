# Grammatical metaphor: theory, lineage, and boundaries

Use this file for definitions, history, subtype boundaries, and theoretical source
routing. Use [gm-decision-protocol.md](gm-decision-protocol.md) for an instance
judgement and [gm-annotation-schema.md](gm-annotation-schema.md) only when a formal
record is requested.

## Contents

1. [Halliday's core criterion](#1-hallidays-core-criterion)
2. [Congruence and counter-tests](#2-congruent-and-metaphorical-are-relational)
3. [Later operational tools](#4-later-operational-tools)
4. [Historical milestones](#5-historical-milestones)
5. [GM types and later extensions](#6-ideational-interpersonal-and-later-extensions)
6. [Lexicalization and language variation](#7-lexicalization-and-language-variation)
7. [Source-use rule](#8-source-use-rule)

## 1. Halliday's core criterion

The theoretical centre is a relation across strata:

```text
semantic category or meaning configuration
                 ⇅ realization
lexicogrammatical category and structure
```

Grammatical metaphor is a non-congruent **re-mapping between semantics and
lexicogrammar**. It is not a property of a word form in isolation. A defensible
analysis therefore needs all of the following:

1. the meaning being construed or enacted in context;
2. the actual lexicogrammatical realization;
3. a plausible, more congruent agnate;
4. an explicit account of the re-mapping.

Typical ideational movements include process or quality construed as Thing and a
logical relation construed within a clause or nominal group. Typical interpersonal
movements include a speech function realized by a non-default Mood choice and a
modal assessment expanded into a projecting clause.

Halliday and Matthiessen's re-mapping account is the definition used by the
`HALLIDAY_CORE` profile. No suffix, dependency relation, POS tag, rank change, or
model probability can replace this cross-stratal evidence.

Primary source: M. A. K. Halliday and Christian M. I. M. Matthiessen, 2014,
*Halliday's Introduction to Functional Grammar*, 4th ed., Ch. 10, Section 10.5.2
“Re-mapping between semantics and lexicogrammar” and Section 10.5.4 “Types of
ideational metaphor” (printed pp. 712, 719; PDF pp. 731, 738 in the supplied
edition).

## 2. Congruent and metaphorical are relational

“Congruent” does not mean simpler, better, literal, or historically earlier in every
case. It identifies a more typical realization within a relevant semantic domain and
register. An agnate is not an exact synonym: it should preserve the central
experience, proposal, polarity, and modal value closely enough that the mapping
contrast is auditable.

Compare:

```text
The population grew rapidly, so pressure on resources rose.
→ The rapid growth of the population brought increased pressure on resources.
```

The second wording can package a process as a referable Thing and realize a logical
relation through a Process. Its nominal form is a signal; the active process meaning,
natural agnate, and re-mapping are the evidence.

## 3. What is not sufficient

The following are candidates or contextual evidence, never automatic GM:

- a noun or derivational suffix;
- nominalization in a morphological sense;
- Chinese zero derivation or the particle `的`;
- embedding or ordinary rank shift;
- a change of Process type;
- technicality, abstraction, brevity, novelty, or frequency;
- lexical metaphor or etymological imagery;
- a high classifier or language-model probability.

Downgrading from clause to group is strong evidence for many ideational cases, but it
is neither sufficient nor necessary for every GM type. An ordinary entity noun, an
ordinary event clause, and an embedded relative clause remain non-GM unless an
independent re-mapping is demonstrated.

## 4. Later operational tools

The following diagnostics are useful later operationalizations. They are **not
Halliday's original terminology**, and they do not displace re-mapping as the core
criterion.

| Tool | Source | Analytical job and limit |
| --- | --- | --- |
| Semantic junction | Wen Li & Bingjun Yang (2024) | Tests whether source meaning remains active while another category's affordances are gained; it still needs contextual evidence and an agnate. |
| Morphological Priority Principle (MPP) | Wen Li & Bingjun Yang (2024) | Selects the closest legitimate agnate for a nominalizing candidate; `PASS` does not prove GM. |
| Full Realization Principle (FRP) | Bingjun Yang (2020), incorporated by Li & Yang (2024) | Distinguishes full, intermediate, and raw compression; it is not a universal interpersonal test. |
| Rank relation | Wen Li & Bingjun Yang (2024) | Records clause-complex → clause/group/word or clause → group/word movement; rank shift alone is not GM. |
| Context-first and AS IF | Bingjun Yang (2019) | Establishes speech function before comparing it with Mood or modality realization. |

Use `HALLIDAY_PLUS_YANG_OPERATIONAL` only when these type-specific tools are part of
the formal annotation profile. Here `YANG` refers to the later Bingjun Yang/Li–Yang
operational work, not Yang Yanning's Chinese descriptive framework. Report both the
Hallidayan mapping decision and the operational results; never let a failed surface
heuristic overrule clear cross-stratal evidence without adjudication.

Later sources:

- Wen Li and Bingjun Yang, 2024, “Towards a system of principles for identifying
  nominalizing metaphors,” *Lingua* 312: 103832, Sections 4–6 (printed/PDF
  pp. 10–18): semantic junction, morphological priority, full realization, and rank
  shift.
- Bingjun Yang, 2020, “Full realization principle for the identification of
  ideational grammatical metaphor: nominalization as example,” *Journal of World
  Languages* 6(3): 161–174 (printed pp. 166–170; PDF pp. 6–10): full,
  intermediate, and raw realization.
- Bingjun Yang, 2019, “Interpersonal metaphor revisited: identification,
  categorization, and syndrome,” *Social Semiotics* 29(2): 186–203 (printed
  pp. 193–199; PDF pp. 9–15): Context-first and AS IF principles.
- Bingjun Yang and Hongmiao Gao, 2023, “Polarity metaphor in English: Definition,
  identification, and categorization,” *Lingua* 295: 103623 (printed/PDF
  pp. 6–13): ideational and interpersonal polarity metaphor.

## 5. Historical milestones

Disambiguate what “first proposed” means:

| Milestone | Date | Verified claim |
| --- | ---: | --- |
| Conceptual precursor | 1966 | Halliday discusses objectification, process nouns, and nominalization before the mature label. |
| Earlier wording | 1976 | `grammatical metaphors` occurs in a broader taxonomy in “Anti-Languages.” |
| Explicit mature naming | 1984 | Halliday names `grammatical metaphor` and contrasts it with lexical metaphor. |
| Systematic textbook account | 1985 | The first edition of *An Introduction to Functional Grammar*, Ch. 10, gives the extended canonical treatment. |

When the question is unqualified, the most precise short answer is: “The earliest
explicit naming of the mature concept verified in the supplied corpus is 1984; 1966
is a precursor, 1976 an earlier broader wording, and 1985 the systematic account.”

Page-verified anchors:

- M. A. K. Halliday, 1966, “Grammar, Society and the Noun,” in Jonathan J.
  Webster (ed.), *On Language and Linguistics: Volume 3 in the Collected Works of
  M. A. K. Halliday* (printed p. 67; PDF p. 80).
- M. A. K. Halliday, 1976, “Anti-Languages,” in Jonathan J. Webster (ed.),
  *Language and Society: Volume 10 in the Collected Works of M. A. K. Halliday*
  (printed p. 278; PDF p. 292).
- M. A. K. Halliday, 1984, “Grammatical Metaphor in English and Chinese,” in
  Jonathan J. Webster (ed.), *Studies in Chinese Language: Volume 8 in the
  Collected Works of M. A. K. Halliday* (printed p. 325; PDF p. 336).

## 6. Ideational, interpersonal, and later extensions

### Ideational

Test a plausible agnate and an explicit meaning-to-grammar re-mapping. Common
patterns include process → Thing, quality → Thing, figure → nominal group, and
logical relation → Process/Thing. Explain effects on agency, tense, causality,
reference, modification, abstraction, and arguability.

### Interpersonal

Determine the enacted exchange before inspecting clause form. An interrogative is
not automatically a metaphorical command; an imperative is not automatically a
congruent command. Co-text, roles, response potential, and the goods-and-services /
information distinction decide the speech function. Then compare it with the Mood
form and a congruent proposal.

### Polarity

Keep Halliday's negative-transfer observation distinct from the later broader model.
Halliday's `I don't think he's coming` is discussed in “Grammatical Metaphor in
English and Chinese” (printed p. 329; PDF p. 340). Yang and Gao later model both
ideational and interpersonal polarity reconstrual.

### Textual and contextual proposals

Treat separate textual or contextual GM categories as disputed extensions. Require a
defensible congruent baseline and show why ordinary Theme/cohesion variation or an
ideational/interpersonal metaphor with textual effects is not the better analysis.
Bingjun Yang, 2018, “Textual Metaphor Revisited,” *Australian Journal of
Linguistics* 38(2): 205–222 (printed pp. 212–219; PDF pp. 9–16).

## 7. Lexicalization and language variation

Lexicalization is gradient. A conventional event noun may still activate a process in
one context and function as an ordinary established entity in another. Dictionary
status is lexical evidence, not a GM verdict.

For Chinese, construct the agnate in natural Chinese. Do not fabricate English-style
derivation. Zero marking, `性/度/率`, `的`, `是……的`, `有……`, and projecting
clauses are evidence to test. When a Chinese nominalizing case uses MPP, preserve
cross-linguistic caution and require human review under the operational profile.

## 8. Source-use rule

This file is a routing map, not a substitute for source verification. Before citing a
theoretical claim to a user, reopen the complete source page or slide and follow
[source-citation-protocol.md](source-citation-protocol.md). Separate Halliday's
primary formulation, later scholars' operational proposals, evidence from the text
being analyzed, and the analyst's inference.
