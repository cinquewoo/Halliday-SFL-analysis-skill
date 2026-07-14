# Halliday SFL Analysis Skill

An installable Codex plugin for evidence-grounded analysis with Hallidayan Systemic Functional Linguistics (SFL).

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

## Repository structure

```text
.agents/plugins/marketplace.json
.agents/skills/halliday-sfl-analyst -> ../../plugins/.../skills/halliday-sfl-analyst
plugins/halliday-sfl-analysis-skill/
├── .codex-plugin/plugin.json
└── skills/halliday-sfl-analyst/
    ├── SKILL.md
    ├── agents/openai.yaml
    └── references/
        ├── theory-core.md
        └── analysis-framework.md
halliday-distillation.md
```

The repository-level symlink keeps the skill directly discoverable while developing inside this repository. Installed users receive the canonical skill bundled under the plugin.

## Sources and redistribution

The plugin includes an original theoretical distillation, procedural framework, and bibliographic page map. It does not redistribute the source PDFs. Users should provide their own legally available texts when exact quotation or pagination needs verification.

## Validate locally

```bash
python3 /path/to/plugin-creator/scripts/validate_plugin.py \
  plugins/halliday-sfl-analysis-skill

python3 /path/to/skill-creator/scripts/quick_validate.py \
  plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst
```
