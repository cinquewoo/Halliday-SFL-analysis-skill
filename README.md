<p align="center">
  <img src="assets/github-hero.svg" alt="Halliday SFL Analyst — meaning choices, congruent alternatives, verifiable sources" width="100%">
</p>

<p align="center">
  <a href="https://github.com/cinquewoo/Halliday-SFL-analysis-skill/releases"><img alt="Release" src="https://img.shields.io/github/v/release/cinquewoo/Halliday-SFL-analysis-skill?display_name=tag&sort=semver&style=flat-square&color=2f81f7"></a>
  <img alt="Codex plugin" src="https://img.shields.io/badge/Codex-installable_plugin-14b8a6?style=flat-square">
  <img alt="Languages" src="https://img.shields.io/badge/analysis-English_%7C_%E4%B8%AD%E6%96%87-d4a72c?style=flat-square">
  <img alt="Source policy" src="https://img.shields.io/badge/sources-page_verified-8b5cf6?style=flat-square">
</p>

<p align="center">
  <strong>Evidence-grounded Hallidayan analysis for English and Chinese.</strong><br>
  From context and metafunctions to grammatical-metaphor diagnostics, congruent alternatives, and complete source locations.
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="#what-it-does">Capabilities</a> ·
  <a href="#try-these-prompts">Examples</a> ·
  <a href="#how-a-claim-is-built">Method</a> ·
  <a href="README.zh-CN.md">中文说明</a>
</p>

---

## Quick start

Add this repository as a Codex plugin marketplace, then install the plugin:

```bash
codex plugin marketplace add cinquewoo/Halliday-SFL-analysis-skill
codex plugin add halliday-sfl-analysis-skill@halliday-sfl
```

Start a new Codex task, then ask:

```text
$halliday-sfl-analyst

Analyze the attached article at full depth. Explain the key meaning choices,
give congruent alternatives for the central clauses, and cite the theory with
complete source titles and verified page locations.
```

> [!TIP]
> The skill also activates implicitly for clear requests about Hallidayan SFL, transitivity, Theme–Rheme, mood and modality, register, or grammatical metaphor.

## What it does

| You ask about | The skill returns |
| --- | --- |
| A text or conversation | Field–tenor–mode, register, three metafunctions, clause complexes, cohesion, and key meaning choices |
| A clause or wording | Systemic-functional analysis, consequential alternatives, and how each alternative changes meaning |
| Grammatical metaphor | Contextual unit, congruent agnate, mapping evidence, counter-test, verdict, confidence, and functional effect |
| Chinese discourse | A dedicated Chinese SFL workflow with language-internal congruent forms and Chinese-specific safeguards |
| Hallidayan theory | A qualified answer with author, year, complete work title, section, and verified page/slide/EPUB location |
| A research corpus | Reproducible sampling, category definitions, counts with denominators, exceptions, and evidence tables |

### Three depths

- **Quick** — context plus 5–10 consequential language choices.
- **Full** — register, three metafunctions, clause complexes, grammatical metaphor, alternatives, and limitations.
- **Research** — reproducible methods, evidence tables, category counts, exceptions, and cautious claims.

## Try these prompts

<details open>
<summary><strong>Full text analysis</strong></summary>

```text
$halliday-sfl-analyst

对我上传的文章进行 full 分析。分别分析概念、人际和语篇意义，解释关键语言选择，
并为核心句提供可比较的替代表达。每个理论判断都给出完整来源和可核验页码。
```

</details>

<details>
<summary><strong>Grammatical-metaphor diagnosis</strong></summary>

```text
$halliday-sfl-analyst

Does “his arrival yesterday” contain grammatical metaphor? Give the congruent
form, apply the identification criteria step by step, state the strongest
counter-analysis, and cite the complete theory sources with printed/PDF pages.
```

</details>

<details>
<summary><strong>Chinese clause analysis</strong></summary>

```text
$halliday-sfl-analyst

判断“经济的快速发展改变了城市结构”是否包含语法隐喻。给出自然的汉语一致式、
映射证据、最强反分析、判定与置信度，并写出完整理论来源及可验证定位。
```

</details>

<details>
<summary><strong>Theory and intellectual history</strong></summary>

```text
$halliday-sfl-analyst

When was grammatical metaphor first proposed? Distinguish the conceptual
precursor, the earlier use of the term, the explicit naming of the mature
phenomenon, and the canonical systematic exposition. Cite primary sources.
```

</details>

## How a claim is built

The skill does not label a form from morphology alone. It follows an auditable evidence chain:

```text
context and speech function
        ↓
meaning and system choice
        ↓
plausible congruent agnate
        ↓
realization mapping + rank relation
        ↓
strongest counter-test
        ↓
qualified verdict + confidence
        ↓
complete, page-verified theory source
```

For grammatical metaphor, the mandatory workflow integrates Halliday's re-mapping account with Yang's Full Realization, Context-first, and AS IF principles, plus Li and Yang's four-system nominalizing-metaphor test. It separates rank shift from metaphor and does not treat every nominalization, embedding, process-type change, or suffix as sufficient evidence.

For historical questions, it also keeps distinct milestones distinct—for example, a conceptual precursor is not automatically the first explicit naming or the first systematic exposition.

## Chinese SFL is a first-class workflow

The dedicated [Chinese analysis framework](plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/references/chinese-sfl-analysis.md) covers Chinese process types, Theme, Mood and modality, clause complexes, zero derivation, ideational transfer candidates, and Chinese mood/modality metaphor.

It requires natural Chinese congruent agnates and does **not** treat `的`, sentence-final particles, `是……的`, `有……`, or `我想／我认为／我觉得……` as automatic metaphor markers.

## Source verification and privacy

Theory answers must name the **actual book, article, chapter, or presentation**—never merely “the PDF”—and provide the most precise verified locator available:

- printed page plus one-based PDF page;
- one-based PPTX slide;
- or EPUB chapter/section plus href/anchor when no fixed page map exists.

The public plugin includes the original analytical framework, source catalog, citation protocol, and indexing utilities. It does **not** redistribute copyrighted books, presentations, extracted source text, absolute local paths, or private indexes. Users map their own legally available sources locally.

See [Private corpus and page verification](docs/private-corpus.md) for archive, integrity-check, indexing, search, and page-label instructions.

## Repository map

```text
.agents/plugins/marketplace.json
.agents/skills/halliday-sfl-analyst → canonical plugin skill
plugins/halliday-sfl-analysis-skill/
├── .codex-plugin/plugin.json
└── skills/halliday-sfl-analyst/
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── references/
    │   ├── analysis-framework.md
    │   ├── chinese-sfl-analysis.md
    │   ├── gm-identification-protocol.md
    │   ├── grammatical-metaphor-research.md
    │   └── source-citation-protocol.md
    └── scripts/
        ├── corpus_index.py
        └── source_archive.py
```

Installed users receive the canonical skill under the plugin. The repository-level symlink keeps it directly discoverable during local development.

## Contributing

Issues and focused pull requests are welcome—especially reproducible false positives/negatives, Chinese counterexamples, source-location corrections, and improvements to analytical transparency. Read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting material, and never upload copyrighted source files.

## Local validation

```bash
python3 /path/to/plugin-creator/scripts/validate_plugin.py \
  plugins/halliday-sfl-analysis-skill

python3 /path/to/skill-creator/scripts/quick_validate.py \
  plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst
```

---

<p align="center">
  Built for analysts who want interpretive depth <em>and</em> an inspectable trail from wording to theory.
</p>
