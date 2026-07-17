# Halliday SFL Analysis Skill

An installable Codex plugin for evidence-grounded analysis with Hallidayan Systemic Functional Linguistics (SFL), including private PDF/PPTX source retention and page/slide-verified citations with complete source titles.

It supports context and register, ideational, interpersonal, and textual metafunctions, clause complexes, grammatical metaphor, alternative wording, English-Chinese analysis safeguards, teaching, and research-oriented review.

The grammatical-metaphor module also distinguishes historical milestones, tests semantic junction rather than suffixes alone, separates rank shift from metaphor, applies Context-first and AS IF diagnostics to interpersonal metaphor, and marks logical, textual, polarity, contextual, and multimodal extensions by lineage and level of consensus.

## Install

Add this repository as a Codex plugin marketplace:

```bash
codex plugin marketplace add cinquewoo/Halliday-SFL-analysis-skill
```

Install the plugin:

```bash
codex plugin add halliday-sfl-analysis-skill@halliday-sfl
```

Start a new Codex task after installation so the skill is loaded.

## Use

Invoke the skill explicitly:

```text
$halliday-sfl-analyst

Analyze the attached article at full depth. Explain the key meaning choices and provide plausible alternative wordings for the central clauses.
```

Chinese example:

```text
$halliday-sfl-analyst

对我上传的文章进行 full 分析，解释关键意义选择，并为核心句提供替代表达。
```

To require source tracing explicitly:

```text
$halliday-sfl-analyst

Explain grammatical metaphor. For every theoretical claim, cite the author, year, complete book/article/presentation title, chapter or section, and verified printed/PDF page or PPTX slide.
```

The skill also allows implicit invocation when a request clearly asks for Hallidayan SFL, metafunction, transitivity, Theme-Rheme, mood/modality, register, or grammatical-metaphor analysis.

## Analysis depths

- **Quick**: Context plus 5-10 consequential language choices.
- **Full**: Context, three metafunctions, clause-complex relations, grammatical metaphor, alternatives, and limitations.
- **Research**: Reproducible sampling, category definitions, counts with denominators, exceptions, evidence tables, and cautious claims.

## Grammatical-metaphor research support

For questions such as “When was grammatical metaphor first proposed?”, the skill avoids collapsing different milestones into one date: 1966 is treated as a conceptual precursor, 1976 as an earlier broader occurrence of the terminology, 1984 as the explicit naming of the mature phenomenon, and 1985 as the canonical systematic exposition.

For identification, it checks a plausible congruent agnate, semantic junction, rank relation, realization degree, morphology, and contextual function. It does not assume that every nominalization, embedded clause, process-type change, or rank shift is automatically a grammatical metaphor.

The detailed workflow is in `references/grammatical-metaphor-research.md`, distilled from Bingjun Yang's 2026 ISFC 51 presentation and cross-checked against page-verified Halliday sources. The source presentation is not redistributed.

## What a full report contains

1. Executive finding.
2. Scope, evidence, and limitations.
3. Field, tenor, mode, and register hypothesis.
4. Ideational analysis.
5. Interpersonal analysis.
6. Textual analysis.
7. Grammatical metaphor and congruent unpacking.
8. Key-choice table with evidence, alternatives, effects, and confidence.
9. Synthesis without unsupported claims about authorial intention.

## Retained and page-verified sources

For theoretical claims, the skill is instructed to:

- preserve supplied PDF/PPTX files in a private content-addressed archive with SHA-256 integrity metadata;
- verify the complete primary-source page or slide and its surrounding context;
- cite the author, year, complete book/article/presentation title, containing volume or venue, and chapter/section when available;
- report both the printed page label and one-based PDF page, or the one-based PPTX slide number;
- distinguish primary evidence, secondary interpretation, text evidence, and analyst inference;
- mark a page/slide as unverified instead of inventing a locator;
- never use a bare filename, source ID, `PDF p. x`, or `slide x` as the complete citation.

The repository defines stable source IDs in `references/corpus-catalog.md`. Users may privately map those IDs to their own legally available PDFs in `.agents/halliday-corpus.local.json`:

```json
{
  "version": 2,
  "sources": [
    {
      "id": "ifg4",
      "title": "Halliday's Introduction to Functional Grammar, 4th edition",
      "full_citation": "Halliday, M. A. K., and Christian M. I. M. Matthiessen. 2014. Halliday's Introduction to Functional Grammar, 4th edition.",
      "short_citation": "Halliday & Matthiessen, IFG4",
      "kind": "pdf",
      "path": "/absolute/path/to/IFG4.pdf"
    }
  ]
}
```

Archive the originals first. The command uses APFS cloning when available and otherwise makes a byte-for-byte copy:

```bash
python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/source_archive.py \
  archive --manifest .agents/halliday-corpus.local.json \
  --destination ~/.codex/halliday-sfl-analysis-sources \
  --output-manifest .agents/halliday-corpus.archived.local.json

python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/source_archive.py \
  verify --manifest .agents/halliday-corpus.archived.local.json
```

Build a private page/slide-level SQLite index from the archived manifest, then search and open the complete supporting unit:

```bash
python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/corpus_index.py \
  build --manifest .agents/halliday-corpus.archived.local.json \
  --database .agents/cache/halliday-corpus.sqlite3

python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/corpus_index.py \
  search --database .agents/cache/halliday-corpus.sqlite3 \
  --source ifg4 --query "resource making meaning"

python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/corpus_index.py \
  page --database .agents/cache/halliday-corpus.sqlite3 \
  --source ifg4 --pdf-page 22

python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/corpus_index.py \
  page --database .agents/cache/halliday-corpus.sqlite3 \
  --source gm-improvements-2026 --slide 103
```

The indexer requires Python and `pypdf`; PPTX text extraction uses the Python standard library. Search hits are candidate evidence: inspect the complete page/slide and visually check scans, OCR, screenshots, tables, diagrams, or uncertain page labels before citing them.

## Repository structure

```text
.agents/plugins/marketplace.json
.agents/skills/halliday-sfl-analyst -> ../../plugins/.../skills/halliday-sfl-analyst
plugins/halliday-sfl-analysis-skill/
├── .codex-plugin/plugin.json
└── skills/halliday-sfl-analyst/
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── references/
    │   ├── analysis-framework.md
    │   ├── corpus-catalog.md
    │   ├── grammatical-metaphor-research.md
    │   ├── source-citation-protocol.md
    │   ├── source-retention.md
    │   └── theory-core.md
    └── scripts/
        ├── corpus_index.py
        └── source_archive.py
halliday-distillation.md
```

The repository-level symlink keeps the skill directly discoverable while developing inside this repository. Installed users receive the canonical skill bundled under the plugin.

## Sources and redistribution

The plugin includes an original theoretical distillation, procedural framework, source catalog, retention utility, citation protocol, and PDF/PPTX indexing utility. The user's supplied source binaries are retained privately with integrity metadata, but the public repository does not redistribute copyrighted books, presentations, absolute local paths, extracted page text, or SQLite indexes. Installed users provide their own legally available copies when exact quotation or pagination needs verification.

## Validate locally

```bash
python3 /path/to/plugin-creator/scripts/validate_plugin.py \
  plugins/halliday-sfl-analysis-skill

python3 /path/to/skill-creator/scripts/quick_validate.py \
  plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst
```
