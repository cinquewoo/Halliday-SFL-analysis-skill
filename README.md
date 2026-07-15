# Halliday SFL Analysis Skill

An installable Codex plugin for evidence-grounded analysis with Hallidayan Systemic Functional Linguistics (SFL), including page-verified primary-source tracing.

It supports context and register, ideational, interpersonal, and textual metafunctions, clause complexes, grammatical metaphor, alternative wording, English-Chinese analysis safeguards, teaching, and research-oriented review.

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

Explain grammatical metaphor. Cite the specific Halliday work, chapter or article, printed page, and one-based PDF page for every theoretical claim.
```

The skill also allows implicit invocation when a request clearly asks for Hallidayan SFL, metafunction, transitivity, Theme-Rheme, mood/modality, register, or grammatical-metaphor analysis.

## Analysis depths

- **Quick**: Context plus 5-10 consequential language choices.
- **Full**: Context, three metafunctions, clause-complex relations, grammatical metaphor, alternatives, and limitations.
- **Research**: Reproducible sampling, category definitions, counts with denominators, exceptions, evidence tables, and cautious claims.

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

## Page-verified Halliday sources

For theoretical claims, the skill is instructed to:

- verify the complete primary-source PDF page and surrounding context;
- cite the work and chapter or article when available;
- report both the printed page label and the one-based PDF page number;
- distinguish primary evidence, secondary interpretation, text evidence, and analyst inference;
- mark pagination as unverified instead of inventing a page number.

The repository defines stable source IDs in `references/corpus-catalog.md`. Users may privately map those IDs to their own legally available PDFs in `.agents/halliday-corpus.local.json`:

```json
{
  "version": 1,
  "sources": [
    {
      "id": "ifg4",
      "title": "Halliday's Introduction to Functional Grammar, 4th edition",
      "short_citation": "Halliday & Matthiessen, IFG4",
      "path": "/absolute/path/to/IFG4.pdf"
    }
  ]
}
```

Build a private page-level SQLite index, then search and open the complete supporting page:

```bash
python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/corpus_index.py \
  build --manifest .agents/halliday-corpus.local.json \
  --database .agents/cache/halliday-corpus.sqlite3

python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/corpus_index.py \
  search --database .agents/cache/halliday-corpus.sqlite3 \
  --source ifg4 --query "resource making meaning"

python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/corpus_index.py \
  page --database .agents/cache/halliday-corpus.sqlite3 \
  --source ifg4 --pdf-page 22
```

The script requires Python and `pypdf`. Search hits are candidate evidence: inspect the complete page, and visually check scans, OCR, tables, or uncertain page labels before citing them.

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
    │   ├── source-citation-protocol.md
    │   └── theory-core.md
    └── scripts/
        └── corpus_index.py
halliday-distillation.md
```

The repository-level symlink keeps the skill directly discoverable while developing inside this repository. Installed users receive the canonical skill bundled under the plugin.

## Sources and redistribution

The plugin includes an original theoretical distillation, procedural framework, source catalog, citation protocol, and indexing utility. It does not redistribute source PDFs, local manifests, extracted page text, or SQLite indexes. Keep those private and provide your own legally available texts when exact quotation or pagination needs verification.

## Validate locally

```bash
python3 /path/to/plugin-creator/scripts/validate_plugin.py \
  plugins/halliday-sfl-analysis-skill

python3 /path/to/skill-creator/scripts/quick_validate.py \
  plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst
```
