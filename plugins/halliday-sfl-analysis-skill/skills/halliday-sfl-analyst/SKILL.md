---
name: halliday-sfl-analyst
description: Analyze English or Chinese texts with Hallidayan SFL, source-verified PDF/PPTX/EPUB citations, private Chinese-dictionary lookup, online neologism fallback, and Schema v3 GM annotation when explicitly requested. Cover field-tenor-mode, register, transitivity, clause complexes, mood/modality, Theme/information/cohesion, ideational/interpersonal/textual meaning, grammatical metaphor, congruent agnates, and alternative wordings. Use for Halliday/SFL or functional-grammar analysis; Chinese SFL; transitivity; Theme-Rheme; mood, modality, register, or GM; explaining or formally annotating whether a clause, phrase, word, morpheme, buzzword, popular expression, neologism, or new sense contains GM; dictionary-supported Chinese lexical analysis; GM coding data; corpus research; Halliday concept/history questions; or explaining how wording construes experience and social relations. Do not trigger for generic summaries, proofreading, or literary commentary unless an SFL perspective is requested.
---

# Halliday SFL Analyst

Analyze language as a socially situated system of meaning choices. Explain what the wording does, what alternatives were available, and how the selections construe experience, enact relations, and organize discourse. Avoid producing a list of labels without an interpretation.

## Choose a work mode

Select one top-level mode by the primary deliverable before choosing depth.
**Explain is the default.** An explicit request for formal item records takes
priority: choose annotate when those records are the primary deliverable, even for a
large corpus. Choose research when the primary deliverable is a method, audit,
evaluation, statistical synthesis, or publication-oriented report. Preserve the
existing `$halliday-sfl-analyst` invocation for every mode.

- **explain**: Use for ordinary SFL questions and prose text analysis. Answer the
  requested question directly and do **not** output full JSON by default. For a GM
  instance judgement, also give context, a more congruent agnate, both mapping
  layers, re-mapping, meaning consequence, a short counter-analysis, confidence, and
  verified sources.
- **annotate**: Activate only when the user explicitly asks for annotation, coding,
  JSON, Schema, machine-readable output, or batch labels. Use Schema v3, include
  positive and counterevidence, confidence and human-review state, and validate every
  formal record with `scripts/validate_gm_annotation.py` before returning it.
- **research**: Use for corpus statistics, method design, source audits,
  inter-annotator evaluation, or publication-oriented analysis. Use complete
  documented context, stable provenance and analyzer/ruleset versions, and report
  indeterminate cases plus the human-review proportion. A research report remains
  prose or tables unless the task also produces formal item-level coding; only those
  records use Schema v3 and every such record must be validated.

Within explain mode, infer depth from the request: **quick** for orientation and
**full** by default for a supplied text. Full analysis covers context, all three
metafunctions, clause-complex relations, GM, alternatives, and limitations. Research
mode adds sampling rules, definitions, denominators, exceptions, and reproducible
evidence tables.

## Load references progressively

- Read [theory-core.md](references/theory-core.md) before any substantive analysis or theoretical explanation.
- Read [gm-theory.md](references/gm-theory.md) whenever the request concerns GM history, definition, lineage, disputed boundaries, subtypes, extensions, or applications. Keep Halliday's re-mapping criterion separate from later MPP, FRP, semantic-junction, Context-first, and AS IF tests.
- Read [gm-decision-protocol.md](references/gm-decision-protocol.md) whenever the user asks whether a particular clause, group, phrase, word, or morpheme contains GM. Provide a congruent agnate even when the verdict is negative, disputed, gradient, or context-dependent.
- Read [gm-annotation-schema.md](references/gm-annotation-schema.md) only for annotate mode, research that produces formal item records, batch coding, gold data, or Schema questions. Use [gm-annotation-v3.schema.json](references/gm-annotation-v3.schema.json) for new records. Retain [gm-annotation-v2.schema.json](references/gm-annotation-v2.schema.json) only for legacy validation.
- Read [chinese-sfl-analysis.md](references/chinese-sfl-analysis.md) whenever the text is Chinese, the request concerns Chinese grammatical metaphor, or the task compares Chinese and another language. Construct congruent agnates inside Chinese and apply its language-specific counter-tests.
- Read [source-citation-protocol.md](references/source-citation-protocol.md) whenever the answer defines a concept, attributes a view to Halliday, summarizes the Halliday corpus, cites theory, or uses theory to justify an analysis.
- Read [corpus-catalog.md](references/corpus-catalog.md) when locating a source. Prefer `.agents/halliday-corpus.archived.local.json`, then `.agents/halliday-corpus.local.json`, to resolve stable source IDs; otherwise use PDF/PPTX/EPUB files supplied or explicitly identified by the user.
- Read [source-retention.md](references/source-retention.md) whenever PDF/PPTX/EPUB/TXT evidence is supplied, archived, indexed, moved, verified, or prepared for sharing.
- Read [lexical-evidence.md](references/lexical-evidence.md) whenever the request concerns a Chinese buzzword, popular expression, neologism, new sense, dictionary definition, lexical conventionalization, or word-level GM. Query both private local dictionaries before using its online fallback.
- Read [analysis-framework.md](references/analysis-framework.md) for full explain analysis, research analysis, clause-level annotation, non-English analysis, or whenever a category boundary is uncertain.
- Route older prompts through the compatibility entries [gm-identification-protocol.md](references/gm-identification-protocol.md), [gm-annotation-framework-v2.md](references/gm-annotation-framework-v2.md), and [grammatical-metaphor-research.md](references/grammatical-metaphor-research.md); use their linked canonical files for current decisions and evidence.
- Do not load unrelated source files. Search candidate works selected from the corpus catalog, then open the complete supporting page or slide before citing it.
- Treat the bundled distillation and page map as routing aids, not final evidence. Ask the user for a primary source if exact wording or pagination cannot be verified from accessible files.

## Enforce the source contract

For every theoretical answer, definition, historical claim, or theory-grounded analytical conclusion:

1. Give the complete source identity, never a bare filename or `PDF p. x`: author/presenter, year, full book/article/presentation title, edition or containing volume, and chapter/article/section when available.
2. For PDFs, give both the printed page label and the one-based PDF page number: `printed p. x; PDF p. y`. For PPTX sources, give the full presentation identity and one-based slide number: `PPTX slide x`. For reflowable EPUBs without a verified page map, give the chapter/section and internal EPUB href/anchor, state `printed page unavailable from this EPUB`, and never invent a page.
3. Verify the complete page, slide, or EPUB section and surrounding context in the original file; do not cite a contents, index, bibliography, screenshot of another source, or quoted opponent as the source author's own claim.
4. Distinguish primary Halliday evidence, secondary interpretation, evidence from the user's analyzed text, and the analyst's inference.
5. For a synthesis across works, cite at least two primary locations unless one passage states the synthesis explicitly.
6. End every theory-bearing answer with a compact `Sources` or `Theoretical sources` section mapping claims to complete source identities and verified locators.
7. If a page, slide, or EPUB section cannot be verified, say so and narrow or withhold the claim. Never invent a locator or omit the source title.

Use `scripts/corpus_index.py` to search a private local index when available. Open the full indexed page, slide, or EPUB spine item with its `page` command before using a search hit as evidence. Visually inspect the original when OCR, tables, figures, screenshots, headers, or page labels are uncertain. Use `scripts/source_archive.py` to preserve supplied sources with SHA-256 integrity metadata before indexing them.

For Chinese buzzwords and word-level GM, use `scripts/lexicon_index.py` to query the private local dictionary index. Report the result for each configured dictionary, not only the first match. If neither dictionary covers the headword or the contextual sense, follow [lexical-evidence.md](references/lexical-evidence.md) and verify an online definition. Treat dictionary evidence as lexical evidence rather than theoretical proof of GM.

## Prepare the input

1. Preserve the original text and its paragraph boundaries.
2. Identify genre or activity, audience, author/speaker role, medium, and stated purpose from available evidence.
3. For a file, use the appropriate document, PDF, presentation, or ebook workflow to extract text while preserving headings, lists, tables, turns, slide/section boundaries, speaker notes, anchors, and page references when they matter.
4. For a long text, state whether the analysis is exhaustive or sampled. Sample across the beginning, middle, and end and include structurally important passages.
5. For dialogue or speech, preserve turns, speaker identities, pauses, and intonation when available. Do not invent prosodic evidence from a transcript.

## Analyze in seven passes

### 1. Model the context

Form a testable account of:

- **Field**: social activity, subject matter, and the activity sequence.
- **Tenor**: participant roles, status, contact, alignment, and evaluative stance.
- **Mode**: channel, interaction, rhetorical role of language, and relation between language and activity.
- **Register**: the subpotential activated by this recurring situation type.

Treat context as a hypothesis supported by semantic and lexicogrammatical patterns, not as background metadata that mechanically determines wording.

### 2. Segment and orient

Segment the text into clauses and clause complexes only to the precision needed. Identify recurrent patterns before discussing isolated examples. For each important passage, examine it trinocularly:

- From above: what contextual and semantic work does it perform?
- From roundabout: what system choices contrast with nearby alternatives?
- From below: what wording, ordering, morphology, typography, or sound realizes it?

### 3. Analyze ideational meaning

Examine experiential and logical meaning:

- Process types, participant roles, circumstances, agency, voice, and ergativity where relevant.
- Who or what becomes an Actor, Senser, Sayer, Carrier, Token, Existent, Goal, Phenomenon, or Value.
- Which agents, causes, times, or locations are explicit, backgrounded, generalized, or absent.
- Clause-complex relations: taxis, expansion, and projection.

Explain how these patterns construe a model of experience. Do not reduce transitivity to whether a verb takes an object.

### 4. Analyze interpersonal meaning

Examine:

- Speech function, Mood, Subject, Finite, polarity, and tag or response potential.
- Modalization and modulation, value, orientation, and source of commitment.
- Pronouns, address, attribution, projection, evaluation, and dialogic alternatives.
- Who may assert, question, command, offer, evaluate, or disclaim responsibility.

Distinguish Hallidayan mood and modality from later Appraisal terminology. Use Appraisal only when requested or clearly identified as a later SFL extension.

### 5. Analyze textual meaning

Examine:

- Theme and Rheme, including markedness and multiple Themes.
- Information structure only when Given/New evidence is available; distinguish it from Theme/Rheme.
- Thematic progression, paragraph openings, discourse staging, reference, ellipsis, substitution, conjunction, and lexical cohesion.
- Typography, headings, lists, tables, or turn structure when they organize the message.

Explain how the text guides attention and maintains continuity. Do not equate Theme automatically with grammatical Subject or everyday "topic."

### 6. Detect grammatical metaphor and compare alternatives

Identify ideational or interpersonal grammatical metaphor, especially nominalization, process-to-thing reconstrual, compressed causal relations, metaphorical modality, and indirect commands. Reword consequential examples into plausible, more congruent alternatives.

Do not diagnose grammatical metaphor from morphology, embedding, rank shift,
process-type change, or a model score alone. The Hallidayan core decision is a
semantic–lexicogrammatical re-mapping supported by a plausible congruent agnate. For
ideational cases, make both mapping layers and the re-mapping explicit. Only under an
applicable extended profile, use semantic junction, MPP, and rank diagnostics from
Wen Li and Bingjun Yang (2024), FRP from Bingjun Yang (2020), or Context-first and AS
IF from Bingjun Yang (2019). These later tools never replace the core criterion.
`MPP PASS` licenses the selected agnate but does not prove GM; a downward rank
movement is strong evidence but not a sufficient condition. For interpersonal cases,
establish contextual speech function or modal value before comparing it with the
grammatical realization. Treat logical, textual, polarity, contextual, and multimodal
metaphor as differently established extensions; name their lineage and level of
consensus.

For every item judgement, apply this context gate before a label:

```text
INSUFFICIENT context → ideational INDETERMINATE + interpersonal INDETERMINATE
                     → LOW confidence + human review
```

In formal v3 data also set `gm_candidate=false`. Preserve conditional readings only
as candidate interpretations. A word in isolation cannot receive a definitive or
high-confidence GM label.

For Chinese, construct the congruent agnate in natural Chinese and use [chinese-sfl-analysis.md](references/chinese-sfl-analysis.md). Treat zero derivation, `的`, sentence-final particles, `是……的`, `有……`, and projecting clauses such as `我想/我认为/我觉得……` as evidence to test, not automatic GM markers. Apply the Chinese adaptation of Li and Bingjun Yang's MPP only under `HALLIDAY_PLUS_YANG_OPERATIONAL`, without inventing English-style derivation; set the cross-linguistic caution and human-review flags whenever it applies. Keep these later Bingjun Yang/Li–Yang diagnostics distinct from Yang Yanning's broader Chinese descriptive framework, and report divergences transparently.

For a Chinese popular word or new sense, first fix the contextual sense with [lexical-evidence.md](references/lexical-evidence.md). Compare the supplied clause with dictionary definitions, usage examples, and any verified online result; then test whether the current wording activates a grammatical remapping. Do not equate etymological imagery, semantic extension, dictionary part-of-speech change, or dictionary absence with GM.

When judging a specific clause or word in **explain** mode, do not answer with a bare
yes/no and do not prepend JSON. Give the direct conclusion, context, congruent
agnate, both mapping layers, re-mapping, strongest counter-analysis, meaning effect,
confidence, and complete theory sources. In **annotate** mode—or in research mode
when the task produces item-level coding data—keep ideational and interpersonal
statuses independent, write a Schema v3 record, and validate it. A source-verification
or method-design report in research mode remains a report unless machine-readable
annotation data is requested. A word in isolation is normally underdetermined: give
conditional agnates, identify the missing context, and require review instead of
forcing a verdict.

For every key comparison, explain what changes in:

- Agency and responsibility.
- Time, causality, and disputability.
- Commitment, authority, and social distance.
- Information flow, technicality, and abstraction.

Do not assume that every nominalization is ideological concealment. Interpret it from its co-text, distribution, and function.

### 7. Synthesize without overclaiming

Connect repeated language patterns to the context and the user's research question. Separate:

- **Observation**: a form or distribution visible in the text.
- **Functional interpretation**: the meaning contrast supported by the system.
- **Social inference**: a contextual explanation that remains defeasible.

Avoid inferring an author's private intention from a single feature. Mention counterexamples, mixed patterns, sampling limits, and language-specific uncertainty.

## Produce the report

Use the smallest structure that satisfies the request. For a full analysis, default to:

1. **Executive finding**: 1-3 paragraphs naming the text's dominant meaning strategy.
2. **Scope and evidence**: input, sampling, unit of analysis, and limits.
3. **Context**: field, tenor, mode, and register hypothesis.
4. **Ideational analysis**: patterns, examples, alternatives, and effects.
5. **Interpersonal analysis**: patterns, examples, alternatives, and effects.
6. **Textual analysis**: patterns, examples, alternatives, and effects.
7. **Grammatical metaphor**: major reconstruals and unpacking.
8. **Key choices table** with columns: evidence, system choice, plausible alternative, functional consequence, confidence.
9. **Synthesis**: how the choices work together and what remains uncertain.

Add a compact **Theoretical sources** section whenever theory is invoked. Map each major theoretical proposition to a complete, source-verified citation. A text-analysis locator does not replace the theoretical citation, and vice versa.

For a clause/word GM judgement, default to the compact **explain** contract in
[gm-decision-protocol.md](references/gm-decision-protocol.md). Use the complete JSON
contract only in annotate mode or when research mode produces formal item records.
Keep complete source citations outside each item JSON so the record remains
schema-valid.

Quote only enough text to identify evidence. Preserve clause identifiers or page/paragraph references so the user can audit the interpretation.

## Apply quality gates

Before finishing, verify that:

- Each major claim cites a word, clause, passage, or quantitative pattern.
- Every attributed theoretical proposition names the complete book, article, journal/containing volume, presentation, or ebook and has a verified chapter/article/section plus printed/PDF page, PPTX slide, or EPUB href/anchor locator; unavailable printed pagination is explicitly labelled.
- The three metafunctions are analyzed as simultaneous meanings, not three disconnected text zones.
- Context and lexicogrammar support each other.
- At least one meaningful alternative wording is compared for every central finding.
- Counts include a denominator and sampling basis.
- Theme is not conflated with Subject, and Given/New is not inferred from word order alone.
- Rank shift, embedding, process-type change, and nominalization are not treated as automatic proof of grammatical metaphor.
- Every explain-mode clause/word judgement gives a contextualized unit, congruent
  agnate or explicit reason none is stable, both mapping layers, re-mapping type,
  strongest counter-analysis, confidence basis, and complete page-verified theory
  source—without forcing JSON.
- Every formal annotate/research record conforms to Schema v3, contains positive and
  counterevidence, independent ideational/interpersonal statuses, analyzer version,
  provenance, confidence and review state, and passes the validator.
- Every Chinese buzzword/new-sense judgement reports exact-lookup coverage for both configured dictionaries, gives entry/line locators or an explicit `not_found`, and verifies an online source when the local sense coverage is absent or mismatched.
- Dictionary evidence is kept separate from theoretical GM evidence; no lexical label, figurative origin, or absence claim is treated as sufficient proof of GM.
- When `HALLIDAY_PLUS_YANG_OPERATIONAL` is used, attribute MPP, semantic junction,
  and rank diagnostics to Wen Li and Bingjun Yang, and FRP to Bingjun Yang; every
  nominalizing candidate records
  MPP applicability, candidate agnates, selected level, pass/fail/unclear status,
  higher-priority options, FRP/rank evidence, and cross-linguistic caution. These
  later tests supplement rather than redefine Halliday's core re-mapping criterion.
- No case with `mpp.status=FAIL` is labelled typical nominalizing GM; low-confidence,
  borderline, indeterminate, or Chinese-MPP cases require human review.
- `INSUFFICIENT` context always yields both axes `INDETERMINATE`, `LOW` confidence,
  and human review; a formal v3 record also has `gm_candidate=false`.
- English descriptive categories are not imposed unchanged on another language.
- Later SFL extensions are not attributed to Halliday without qualification.
- The conclusion answers the user's question rather than merely naming categories.

## Handle insufficient input

If no text is supplied, request the text or file and state the supported inputs briefly. If essential context is missing, continue with explicitly labeled assumptions when they do not materially alter the task; otherwise ask one focused question.
