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
| Grammatical metaphor | Schema-valid v2 JSON, independent ideational/interpersonal labels, MPP evidence, congruent agnate, counterevidence, confidence, and review status |
| Chinese discourse | A dedicated Chinese SFL workflow with language-internal congruent forms and Chinese-specific safeguards |
| A Chinese buzzword or new sense | Exact coverage from both configured private dictionaries, contextual sense evidence, a bounded online fallback when needed, and a separate GM judgement |
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
form, return the v2 annotation JSON, apply MPP and the other identification
criteria, state the strongest counter-analysis, and cite complete theory sources.
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
<summary><strong>Chinese buzzword and dictionary evidence</strong></summary>

```text
$halliday-sfl-analyst

从语法隐喻角度分析“游客纷纷来这里打卡”中的“打卡”。先分别查询《现代汉语词典》
第7版和侯敏《汉语新词语词典（2000—2020）》；若语境义仍未覆盖，再核验在线新词语库。
给出词条定位、自然汉语一致式、v2 JSON、最强反分析和页码经过核验的理论来源。
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
congruent agnate candidates
        ↓
MPP selection + realization mapping
        ↓
rank + FRP + semantic junction / AS IF
        ↓
exclusions + strongest counterevidence
        ↓
independent labels + confidence + review
        ↓
complete, page-verified theory source
```

For grammatical metaphor, the mandatory workflow integrates Halliday's re-mapping account with Yang's Full Realization, Context-first, and AS IF principles, plus Li and Yang's four-system nominalizing-metaphor test. Morphological Priority Principle (MPP) is now a strict agnate-selection gate for nominalizing candidates: direct derivation precedes `-ing`/infinitival agnation, which precedes non-morphological agnation. An MPP pass does not prove GM; typical nominalizing GM must also pass rank, full-realization, semantic-junction, and exclusion gates.

### Reproducible GM annotation

Each item-level judgement returns a stable JSON contract with:

- separate `ideational_gm_status` and `interpersonal_gm_status`;
- polarity as an independent co-occurring annotation;
- candidate and selected agnates, MPP level and status;
- rank shift, Full Realization, semantic junction, Context-first/AS IF evidence;
- exclusions, positive evidence, counterevidence, confidence, and human-review status.

Chinese MPP uses a cautious language-internal ordering and always requires a cross-linguistic caution flag plus human review. Saved or batch records can be checked with the bundled validator:

```bash
python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/validate_gm_annotation.py \
  annotation.json
```

For historical questions, it also keeps distinct milestones distinct—for example, a conceptual precursor is not automatically the first explicit naming or the first systematic exposition.

## Chinese SFL is a first-class workflow

The dedicated [Chinese analysis framework](plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/references/chinese-sfl-analysis.md) covers Chinese process types, Theme, Mood and modality, clause complexes, zero derivation, ideational transfer candidates, and Chinese mood/modality metaphor.

It requires natural Chinese congruent agnates and does **not** treat `的`, sentence-final particles, `是……的`, `有……`, or `我想／我认为／我觉得……` as automatic metaphor markers.

## Dictionary-backed Chinese buzzword analysis

The [lexical-evidence protocol](plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/references/lexical-evidence.md) fixes the contextual sense before testing GM:

1. query both locally configured dictionaries and retain every homograph and sense marker;
2. report each dictionary's exact-match status and TXT line locator;
3. if neither dictionary covers the contextual sense, perform one bounded exact lookup in the China Media University new-word research database;
4. keep dictionary/web evidence separate from the Hallidayan evidence used to decide GM.

Dictionary inclusion, absence, figurative origin, semantic extension, and part-of-speech labels do not by themselves prove or disprove grammatical metaphor. A TXT line is reported as a TXT line—never converted into an invented printed page.

The plugin ships the private indexing and online-adapter code, not the dictionaries. Users build the index from legally obtained local texts; a user-level index under `~/.codex` can then be discovered from new tasks and other projects.

## Source verification and privacy

Theory answers must name the **actual book, article, chapter, or presentation**—never merely “the PDF”—and provide the most precise verified locator available:

- printed page plus one-based PDF page;
- one-based PPTX slide;
- EPUB chapter/section plus href/anchor when no fixed page map exists;
- or dictionary headword plus supplied-TXT line span when no printed-page map can be verified.

The public plugin includes the original analytical framework, source catalog, citation protocol, and indexing utilities. It does **not** redistribute copyrighted books, dictionaries, presentations, extracted source text, absolute local paths, or private indexes. Users map their own legally available sources locally.

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
    │   ├── gm-annotation-framework-v2.md
    │   ├── gm-annotation-v2.schema.json
    │   ├── gm-identification-protocol.md
    │   ├── grammatical-metaphor-research.md
    │   ├── lexical-evidence.md
    │   ├── source-retention.md
    │   └── source-citation-protocol.md
    └── scripts/
        ├── corpus_index.py
        ├── cuc_newword_lookup.mjs
        ├── lexicon_index.py
        ├── source_archive.py
        ├── test_cuc_newword_lookup.mjs
        ├── test_lexicon_index.py
        ├── test_source_archive.py
        └── validate_gm_annotation.py
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

python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/validate_gm_annotation.py \
  annotation.json

python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/test_lexicon_index.py
python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/test_source_archive.py
node plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/test_cuc_newword_lookup.mjs
```

---

<p align="center">
  Built for analysts who want interpretive depth <em>and</em> an inspectable trail from wording to theory.
</p>
