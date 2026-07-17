# Grammatical-metaphor instance identification protocol

Use this protocol whenever the user asks whether a clause, group, phrase, word, morpheme, or short wording contains grammatical metaphor (GM). The task is relational: a visible form is not GM by itself. The analysis must establish a meaning in context, a plausible congruent agnate, and the non-congruent realization that relates them.

## Mandatory result

Every instance judgement must provide:

1. **Analysed unit and co-text.** Quote the smallest auditable unit and state the context used. A word without a clause is normally underdetermined.
2. **Candidate type and lineage.** Name ideational, interpersonal, polarity, or disputed textual GM, and distinguish Halliday's account from a later refinement.
3. **Congruent agnate/form.** Give the most plausible congruent wording that preserves the relevant contextual meaning. Call it an *agnate*, not an exact synonym.
4. **Identification evidence.** Show the semantic-to-lexicogrammatical relation step by step, using the type-specific tests below.
5. **Counter-test.** State the strongest reason the item might not be GM and why that alternative was accepted or rejected.
6. **Verdict.** Use `GM`, `partly/gradient GM`, `not GM`, `disputed`, or `insufficient context`; add high, medium, or low confidence with a reason.
7. **Meaning consequence.** Explain what the selected wording changes in agency, time, causality, abstraction, reference, negotiability, arguability, commitment, or information flow.
8. **Verified theory source.** Give the complete book/article title and exact printed/PDF pages under the citation protocol.

Do not replace this reasoning with a suffix, word-class, or dependency label.

## Common first pass

### 1. Establish contextual meaning

Identify what is being construed or enacted before inspecting its grammatical form:

- experience: process, quality, circumstance, entity, or logical relation;
- exchange: statement, question, command, or offer;
- modality: probability, usuality, obligation, or inclination;
- polarity: the negative meaning at issue;
- textual organization: the proposed textual relation or information effect.

Use surrounding clauses, genre, participant roles, and actual or expected responses. If these materially affect the classification but are missing, give conditional analyses rather than inventing one context.

### 2. Construct a congruent agnate

Unpack the candidate into a natural wording that realizes the relevant meaning more directly. Preserve participants, polarity, modal value, and logical relation where they matter. A good agnate need not preserve every rhetorical effect; the lost or gained effect is part of the analysis.

If a restrictive relative, referring expression, or other embedded unit has no equivalent single-clause agnate, say so and use the smallest natural multi-clause expansion. Do not treat the unavoidable change in discourse function as proof of GM.

Reject an agnate that is ungrammatical, changes the key proposition or proposal, depends on a remote synonym while a direct morphological relation is available, or exists only to force a metaphor judgement.

For an isolated word, embed it in the supplied clause. If no clause is supplied, give one or more conditional agnates and conclude `insufficient context`, for example:

```text
development
- process reading: X developed Y → the development of Y by X
- established entity/field reading: may be lexicalized and not active GM
```

### 3. Compare mapping and affordances

State both sides of the relation:

```text
contextual semantic value → lexicogrammatical realization
congruent semantic value  → congruent realization
```

Then test whether the selected wording carries a **semantic junction**: the earlier semantic value remains active while the grammar adds affordances of another category. A process construed as a thing, for example, can become definite, plural, quantified, modified, classified, referred to, or thematized while still denoting a process.

Halliday and Matthiessen describe ideational GM as re-mapping between semantics and lexicogrammar and show its typical downgrading from sequence to figure, figure to element, clause nexus to clause, clause to group/phrase, and group/phrase to word. This is the Hallidayan base; the further tests below are later operational refinements. See *Halliday's Introduction to Functional Grammar*, 4th ed., `10.5.2 Re-mapping between semantics and lexicogrammar` and `10.5.4 Types of ideational metaphor` (printed pp. 712, 719; PDF pp. 731, 738).

## Chinese-language branch

For Chinese material, read [chinese-sfl-analysis.md](chinese-sfl-analysis.md) and apply these safeguards before the type-specific tests:

1. Construct the congruent agnate in natural Chinese; do not translate to English to create the decisive contrast.
2. Treat zero derivation, `的`, nominal-group position, `性/率/度`, sentence-final particles, `是……的`, `有……`, and `我想/我认为/我觉得……` as clues, not automatic GM markers.
3. Analyze the whole verb group, including result and directional complements, before deciding whether a process has changed category.
4. Distinguish existential `有`, possessive/relational `有`, and `有` used to introduce an indefinite participant.
5. For mood and modality, establish the contextual speech function and response potential before interpreting interrogative constructions or particles.
6. Report Yang Yanning's Chinese category and the stricter protocol verdict separately when they diverge. In particular, her “add Thing” and “add Process” types lack a direct congruent form in that framework and are therefore disputed under this protocol unless a natural agnate can be recovered.

Yang Yanning's Chinese descriptive framework is located in *汉语语法隐喻研究*, Chapters 3-5, especially 4.4-4.5 and 5.1-5.3 (EPUB section hrefs listed in [chinese-sfl-analysis.md](chinese-sfl-analysis.md); printed pages unavailable from the supplied reflowable EPUB).

## Nominalizing and other ideational GM

For a canonical nominalizing metaphor, test four complementary systems. No single test is sufficient.

| Test | Required question | Positive evidence | Common false positive |
| --- | --- | --- | --- |
| Semantic junction | Is entity meaning fused with process, quality, circumstance, or relator meaning? | `develop → development`, with both event and thing-like reference active | product, agent, patient, instrument, location, or measure noun with no active junction |
| Morphological priority | Is the closest legitimate agnate being compared? | derivational agnation first; then `-ing`/infinitival for a lexical gap; non-morphological only where needed | choosing a remote synonym although a direct derivative exists |
| Full realization | Is the figure compressed in meaning **and** form? | clause/sequence realized as a nominal group or word | a finite embedded clause compressed only semantically |
| Rank shift | What lower-ranked unit realizes the meaning? | clause complex → clause/group/word; clause → group/word | rankshifted embedding without semantic-grammatical reconstrual |

Report realization degree explicitly:

- **Full:** compressed in meaning and form; eligible for canonical ideational GM if the other tests also pass.
- **Intermediate:** partly compressed; report as partly/gradient GM, not a canonical case.
- **Raw:** compressed only in meaning while retaining clausal form; do not classify as GM merely because it is embedded.

Use the four systems together. Li and Yang propose concurrent choices in SEMANTIC JUNCTION, MORPHOLOGICAL PRIORITY, FULL REALIZATION, and RANK SHIFT, and show the integrated system and examples on printed pp. 16-18 (PDF pp. 16-18) of *Towards a system of principles for identifying nominalizing metaphors*. Yang develops the full/intermediate/raw distinction and the embedding counter-test on printed pp. 166-170 (PDF pp. 6-10) of *Full realization principle for the identification of ideational grammatical metaphor: nominalization as example*.

### Exclusion checks

Do not classify a candidate as GM solely because it is:

- a noun with `-tion`, `-ment`, `-ness`, `-ing`, or another nominal morphology;
- an event noun that cannot be naturally unpacked into a clause;
- a product, agent, patient, instrument, location, or measure noun without an active semantic junction;
- a technicalized or lexicalized label whose process/quality/relation meaning is no longer active in the current use;
- a finite nominal, projected, relative, or WH-clause;
- a non-finite nominal clause without enough compression for full realization;
- an embedded or rankshifted unit;
- a change in Process type;
- a shell noun whose following complement, rather than the shell noun, carries any relevant reconstrual.

Lexicalization is gradient. Do not call a metaphor “dead” from dictionary status or intuition alone; use current contextual meaning, agnation, and available evidence.

## Mood and modality metaphor

Start from meaning exchange, not clause form.

### Context-first test

1. Determine whether the speaker is giving or demanding information or goods-and-services.
2. Use co-text and response potential: answer, agreement, challenge, compliance, acceptance, or refusal.
3. Identify the default congruent Mood in that context.
4. Compare the selected Mood with the enacted speech function.

Typical congruent pairings are statement–declarative, question–interrogative, command–imperative, and offer–modalized interrogative or declarative. They are baselines, not context-free labels.

### AS IF test

Ask whether the selected wording is functioning **as if** it realized another default value. If an interrogative enacts a command, provide the imperative agnate; if an imperative gives information, provide the declarative agnate. Explain the change in negotiability, arguability, authority, acceptability, or politeness without assuming that indirectness is always polite.

For modality, identify the contextual modal value before the grammatical orientation. A projecting clause such as `I think ...` may realize probability, while the same form in professional advice may function as an attenuated obligation. Give the congruent modal or proposal wording that matches the enacted value.

Yang defines the Context-first and AS IF principles on printed pp. 193-195 (PDF pp. 9-11), applies them across four speech functions on printed pp. 195-197 (PDF pp. 11-13), and states their joint identification role on printed p. 199 (PDF p. 15) of *Interpersonal metaphor revisited: identification, categorization, and syndrome*.

## Polarity metaphor

First identify the negative meaning, then give a direct congruent negative agnate. Diagnose the indirect realization along one or both lines:

- **Ideational polarity GM:** negative meaning is reconstrued as participation, processation, qualification, or circumstantiation through transcategorization or rank shift.
- **Interpersonal polarity GM:** negative meaning is realized through tension with mood/speech function or through a metaphorical modality choice.

Affixes and negative vocabulary are not sufficient by themselves. Test the contextual negative meaning, mapping, semantic junction or interpersonal AS IF relation, and the direct negative agnate. If both lines operate, report the primary analysis and the secondary interpersonal effect rather than forcing a single label.

Yang and Gao define polarity metaphor as indirect reconstrual of negative meaning on printed p. 6 (PDF p. 6), describe the four ideational realizations on printed pp. 7-8 (PDF pp. 7-8), mood and modality tests on printed pp. 8-10 (PDF pp. 8-10), and summarize the combined model on printed p. 13 (PDF p. 13) of *Polarity metaphor in English: Definition, identification, and categorization*.

## Proposed textual metaphor

Treat textual GM as disputed. A change in Theme, cohesion, information flow, reference, or text organization is not enough. Before assigning a separate textual-GM label, require all three:

1. a one-to-one or otherwise defensible congruent textual baseline;
2. an identification principle that distinguishes the case from ordinary marked Theme or textual variation;
3. evidence that ideational or interpersonal GM with textual effects does not explain the case more economically.

If these tests fail, report `ideational/interpersonal GM with textual effects`, `textual variation`, or `disputed`, not a confident textual-GM verdict. Yang identifies the lack of a congruent baseline, overlap with ideational metaphor, nominalization dominance, weak tests, and an undefined unique function on printed pp. 212-218 (PDF pp. 9-15), and argues that the separate category is redundant for current meaning creation and analysis on printed p. 219 (PDF p. 16) of *Textual Metaphor Revisited*.

## Decision table

Use this compact table in clause/word answers:

| Field | Required content |
| --- | --- |
| Unit + context | exact wording and the co-text/function assumed |
| Candidate | GM lineage and subtype |
| Congruent agnate | natural, meaning-matched unpacking |
| Mapping evidence | semantic value → selected grammar vs congruent grammar |
| Type-specific tests | four nominalizing systems, Context-first/AS IF, polarity mapping, or textual safeguards |
| Counter-test | strongest non-GM analysis |
| Verdict | GM / partly GM / not GM / disputed / insufficient context + confidence |
| Meaning consequence | what becomes more/less explicit, temporal, agentive, abstract, referable, arguable, or negotiable |

## Source map

- Halliday, M. A. K., and Christian M. I. M. Matthiessen. 2014. *Halliday's Introduction to Functional Grammar*, 4th ed., Ch. 10, `10.5.2 Re-mapping between semantics and lexicogrammar` and `10.5.4 Types of ideational metaphor` (printed pp. 712, 719; PDF pp. 731, 738).
- Li, Wen, and Bingjun Yang. 2024. `Towards a system of principles for identifying nominalizing metaphors`. *Lingua* 312: 103832, Sections 4-6 (printed pp. 10-18; PDF pp. 10-18). https://doi.org/10.1016/j.lingua.2024.103832.
- Yang, Bingjun. 2020. `Full realization principle for the identification of ideational grammatical metaphor: nominalization as example`. *Journal of World Languages* 6(3): 161-174, Sections 4-6 (printed pp. 166-170; PDF pp. 6-10). https://doi.org/10.1080/21698252.2020.1777682.
- Yang, Bingjun. 2019. `Interpersonal metaphor revisited: identification, categorization, and syndrome`. *Social Semiotics* 29(2): 186-203 (printed pp. 193-199; PDF pp. 9-15). https://doi.org/10.1080/10350330.2018.1425322.
- Yang, Bingjun, and Hongmiao Gao. 2023. `Polarity metaphor in English: Definition, identification, and categorization`. *Lingua* 295: 103623, Sections 3-6 (printed pp. 6-13; PDF pp. 6-13). https://doi.org/10.1016/j.lingua.2023.103623.
- Yang, Bingjun. 2018. `Textual Metaphor Revisited`. *Australian Journal of Linguistics* 38(2): 205-222, Sections 3-4 (printed pp. 212-219; PDF pp. 9-16). https://doi.org/10.1080/07268602.2018.1400502.
- 杨延宁. 2020. 《汉语语法隐喻研究》. 北京：北京大学出版社，Chs. 3-5, especially 4.4-4.5 and 5.1-5.3 (EPUB section hrefs in [chinese-sfl-analysis.md](chinese-sfl-analysis.md); printed pages unavailable from the supplied reflowable EPUB).
