---
name: halliday-sfl-analyst
description: Analyze written or spoken texts with Hallidayan Systemic Functional Linguistics (SFL), with page-verified PDF/PPTX source tracing and complete bibliographic citations. Cover field-tenor-mode, register, ideational meaning and transitivity, interpersonal meaning and mood/modality, textual meaning and Theme/information/cohesion, clause complexes, grammatical metaphor, congruent forms, and meaningful alternative wordings. Use for Halliday/SFL analysis, metafunction analysis, functional grammar, transitivity, Theme-Rheme, mood or modality, register, grammatical metaphor, deciding whether a clause or word contains grammatical metaphor, questions about Halliday's concepts or intellectual development, and theory-grounded explanations of how wording construes experience and social relations. Do not trigger for generic summaries, proofreading, or literary commentary unless the user asks for an SFL perspective.
---

# Halliday SFL Analyst

Analyze language as a socially situated system of meaning choices. Explain what the wording does, what alternatives were available, and how the selections construe experience, enact relations, and organize discourse. Avoid producing a list of labels without an interpretation.

## Choose an analysis depth

Infer the depth from the request. Use **full** when the user does not specify one.

- **Quick**: Analyze the context and 5-10 consequential choices. Use for short answers or orientation.
- **Full**: Analyze context, all three metafunctions, clause-complex relations, grammatical metaphor, key alternatives, and limitations. Use representative examples rather than tagging every clause of a long text.
- **Research**: Add an explicit sampling method, category definitions, counts with denominators, exceptions, reproducible evidence tables, and cautious claims. Use for theses, papers, corpus comparisons, or publication-oriented work.

## Load references progressively

- Read [theory-core.md](references/theory-core.md) before any substantive analysis or theoretical explanation.
- Read [grammatical-metaphor-research.md](references/grammatical-metaphor-research.md) whenever the request concerns the history, identification, disputed boundaries, subtypes, research extensions, or applications of grammatical metaphor.
- Read [gm-identification-protocol.md](references/gm-identification-protocol.md) whenever the user asks whether a particular clause, group, phrase, word, or morpheme contains grammatical metaphor. Follow its mandatory result format and provide a congruent agnate even when the verdict is negative, disputed, gradient, or context-dependent.
- Read [source-citation-protocol.md](references/source-citation-protocol.md) whenever the answer defines a concept, attributes a view to Halliday, summarizes the Halliday corpus, cites theory, or uses theory to justify an analysis.
- Read [corpus-catalog.md](references/corpus-catalog.md) when locating a source. Prefer `.agents/halliday-corpus.archived.local.json`, then `.agents/halliday-corpus.local.json`, to resolve stable source IDs; otherwise use PDF/PPTX files supplied or explicitly identified by the user.
- Read [source-retention.md](references/source-retention.md) whenever PDF/PPTX evidence is supplied, archived, indexed, moved, verified, or prepared for sharing.
- Read [analysis-framework.md](references/analysis-framework.md) for full or research analysis, clause-level annotation, non-English analysis, or whenever a category boundary is uncertain.
- Do not load unrelated source files. Search candidate works selected from the corpus catalog, then open the complete supporting page or slide before citing it.
- Treat the bundled distillation and page map as routing aids, not final evidence. Ask the user for a primary source if exact wording or pagination cannot be verified from accessible files.

## Enforce the source contract

For every theoretical answer, definition, historical claim, or theory-grounded analytical conclusion:

1. Give the complete source identity, never a bare filename or `PDF p. x`: author/presenter, year, full book/article/presentation title, edition or containing volume, and chapter/article/section when available.
2. For PDFs, give both the printed page label and the one-based PDF page number: `printed p. x; PDF p. y`. For PPTX sources, give the full presentation identity and one-based slide number: `PPTX slide x`.
3. Verify the complete page or slide and surrounding context in the original file; do not cite a contents, index, bibliography, screenshot of another source, or quoted opponent as the source author's own claim.
4. Distinguish primary Halliday evidence, secondary interpretation, evidence from the user's analyzed text, and the analyst's inference.
5. For a synthesis across works, cite at least two primary locations unless one passage states the synthesis explicitly.
6. End every theory-bearing answer with a compact `Sources` or `Theoretical sources` section mapping claims to complete source identities and verified locators.
7. If a page or slide cannot be verified, say `page/slide unverified` and narrow or withhold the claim. Never invent a locator or omit the source title.

Use `scripts/corpus_index.py` to search a private local index when available. Open the full indexed page or slide with its `page` command before using a search hit as evidence. Visually inspect the original when OCR, tables, figures, screenshots, headers, or page labels are uncertain. Use `scripts/source_archive.py` to preserve supplied sources with SHA-256 integrity metadata before indexing them.

## Prepare the input

1. Preserve the original text and its paragraph boundaries.
2. Identify genre or activity, audience, author/speaker role, medium, and stated purpose from available evidence.
3. For a file, use the appropriate document, PDF, or presentation workflow to extract text while preserving headings, lists, tables, turns, slide boundaries, speaker notes, and page references when they matter.
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

Do not diagnose grammatical metaphor from morphology, embedding, rank shift, or process-type change alone. For ideational cases, test the congruent agnate, semantic junction, rank relation, and degree of realization. For interpersonal cases, establish the contextual speech function or modal value before comparing it with the grammatical realization. Treat logical, textual, polarity, contextual, and multimodal metaphor as differently established extensions; name their lineage and level of consensus.

When judging a specific clause or word, do not answer with a bare yes/no. Quote the analysed unit and context; name the candidate lineage; give the congruent agnate; show the semantic-to-grammatical mapping and type-specific tests; state the strongest counter-analysis; report `GM`, `partly/gradient GM`, `not GM`, `disputed`, or `insufficient context` with confidence; and cite the complete theory source with verified pages. A word in isolation is normally underdetermined: give conditional agnates and identify the missing context instead of forcing a verdict.

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

Add a compact **Theoretical sources** section whenever theory is invoked. Map each major theoretical proposition to a complete, page/slide-verified citation. A text-analysis locator does not replace the theoretical citation, and vice versa.

For a clause/word GM judgement, default to the decision table in [gm-identification-protocol.md](references/gm-identification-protocol.md), even when the rest of the answer is brief.

Quote only enough text to identify evidence. Preserve clause identifiers or page/paragraph references so the user can audit the interpretation.

## Apply quality gates

Before finishing, verify that:

- Each major claim cites a word, clause, passage, or quantitative pattern.
- Every attributed theoretical proposition names the complete book, article, journal/containing volume, or presentation and has a verified chapter/article/section plus printed/PDF page or PPTX slide locator; unverified locations are explicitly labelled.
- The three metafunctions are analyzed as simultaneous meanings, not three disconnected text zones.
- Context and lexicogrammar support each other.
- At least one meaningful alternative wording is compared for every central finding.
- Counts include a denominator and sampling basis.
- Theme is not conflated with Subject, and Given/New is not inferred from word order alone.
- Rank shift, embedding, process-type change, and nominalization are not treated as automatic proof of grammatical metaphor.
- Every clause/word GM judgement includes a contextualized unit, congruent agnate, positive evidence, counter-test, explicit verdict, confidence basis, functional consequence, and complete page-verified theory source.
- English descriptive categories are not imposed unchanged on another language.
- Later SFL extensions are not attributed to Halliday without qualification.
- The conclusion answers the user's question rather than merely naming categories.

## Handle insufficient input

If no text is supplied, request the text or file and state the supported inputs briefly. If essential context is missing, continue with explicitly labeled assumptions when they do not materially alter the task; otherwise ask one focused question.
