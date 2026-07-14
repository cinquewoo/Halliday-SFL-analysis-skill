---
name: halliday-sfl-analyst
description: Analyze written or spoken texts with Hallidayan Systemic Functional Linguistics (SFL), covering field-tenor-mode, register, ideational meaning and transitivity, interpersonal meaning and mood/modality, textual meaning and Theme/information/cohesion, clause complexes, grammatical metaphor, and meaningful alternative wordings. Use when a user requests Halliday/SFL analysis, metafunction analysis, functional grammar, transitivity, Theme-Rheme, mood or modality, register analysis, grammatical metaphor, or a theory-grounded explanation of how wording construes experience and social relations. Do not trigger for generic summaries, proofreading, or literary commentary unless the user asks for an SFL perspective.
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
- Read [analysis-framework.md](references/analysis-framework.md) for full or research analysis, clause-level annotation, non-English analysis, or whenever a category boundary is uncertain.
- Do not load unrelated source PDFs. Ask the user to supply any source whose exact wording or pagination must be checked.

## Prepare the input

1. Preserve the original text and its paragraph boundaries.
2. Identify genre or activity, audience, author/speaker role, medium, and stated purpose from available evidence.
3. For a file, use the appropriate document or PDF workflow to extract text while preserving headings, lists, tables, turns, and page references when they matter.
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

Quote only enough text to identify evidence. Preserve clause identifiers or page/paragraph references so the user can audit the interpretation.

## Apply quality gates

Before finishing, verify that:

- Each major claim cites a word, clause, passage, or quantitative pattern.
- The three metafunctions are analyzed as simultaneous meanings, not three disconnected text zones.
- Context and lexicogrammar support each other.
- At least one meaningful alternative wording is compared for every central finding.
- Counts include a denominator and sampling basis.
- Theme is not conflated with Subject, and Given/New is not inferred from word order alone.
- English descriptive categories are not imposed unchanged on another language.
- Later SFL extensions are not attributed to Halliday without qualification.
- The conclusion answers the user's question rather than merely naming categories.

## Handle insufficient input

If no text is supplied, request the text or file and state the supported inputs briefly. If essential context is missing, continue with explicitly labeled assumptions when they do not materially alter the task; otherwise ask one focused question.
