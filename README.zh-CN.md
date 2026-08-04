<p align="center">
  <img src="assets/github-hero.svg" alt="Halliday SFL Analyst：意义选择、一致式替换与可核验来源" width="100%">
</p>

<p align="center">
  <strong>面向英语与汉语的、证据可追溯的韩礼德系统功能语言学分析插件。</strong><br>
  从语境与三大元功能，到语法隐喻识别、一致式替换和完整出处定位。
</p>

<p align="center">
  <a href="https://github.com/cinquewoo/Halliday-SFL-analysis-skill/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/cinquewoo/Halliday-SFL-analysis-skill/ci.yml?branch=main&style=flat-square&label=CI"></a>
  <img alt="GM Schema" src="https://img.shields.io/badge/GM_Schema-v3.0-f97316?style=flat-square">
</p>

<!-- plugin-version: 1.4.0 -->

<p align="center">
  <a href="README.md">English</a> ·
  <a href="#30-秒安装">快速安装</a> ·
  <a href="#核心能力">核心能力</a> ·
  <a href="#可直接复制的提问">提问示例</a> ·
  <a href="#来源核验与隐私">来源核验</a>
</p>

## 30 秒安装

```bash
codex plugin marketplace add cinquewoo/Halliday-SFL-analysis-skill
codex plugin add halliday-sfl-analysis-skill@halliday-sfl
```

安装后新建一个 Codex 任务：

```text
$halliday-sfl-analyst

对我上传的文章进行 full 分析。解释关键意义选择，为核心句提供一致式和替代表达；
每个理论判断都给出完整书名或论文名，以及经过核验的具体页码。
```

## 核心能力

| 输入 | 输出 |
| --- | --- |
| 文章、对话或多模态材料 | 语场—语旨—语式、语域、三大元功能、小句复合体、衔接与关键意义选择 |
| 一个小句或词组 | 系统功能分析、可比较替换形式，以及每种表达改变了什么意义 |
| “这是不是语法隐喻？” | 默认直接给出解释性结论；只有明确要求正式标注或机器可读编码时才输出 Schema v3 |
| 汉语语篇 | 独立的汉语 SFL 工作流、自然汉语一致式和汉语专属识别约束 |
| 汉语流行语、新词或新义 | 两部私有词典的逐源精确检索、语境义证据、必要时受限在线补查，以及与词义证据分开的 GM 判定 |
| 理论或学术史问题 | 作者、年份、完整书籍／论文／演示文稿名称、章节和核验页码 |
| 研究语料 | 可复现抽样、类别定义、分母明确的计数、例外和证据表 |

工作模式分为：**explain**（默认，普通问答和文本分析，不强制 JSON）、**annotate**（用户明确要求标注、编码、JSON、Schema 或批量标签）和 **research**（语料统计、方法、来源审计与评测）。`quick`／`full` 是 explain 的分析深度；research 只有在逐项编码时才使用 JSONL／CSV。

## 可直接复制的提问

### 全文分析

```text
$halliday-sfl-analyst

按照 full 深度分析这篇文章，分别给出概念、人际和语篇分析；解释关键语言选择，
为核心句提供替代表达，并说明替换后意义如何变化。
```

### 语法隐喻识别

```text
$halliday-sfl-analyst

判断“经济的快速发展改变了城市结构”是否包含语法隐喻。给出自然的汉语一致式、
说明语义层与词汇语法层的映射、重映射类型、最强反分析、判定与置信度，
并写出完整理论来源及可验证定位。
```

### 正式 Schema v3 标注

```text
$halliday-sfl-analyst

把“A decision was made”标注为 Schema v3 JSON：写出候选跨度、一致式、两层映射、
重映射类型、正证、反证、置信度和人工复核状态；返回前运行校验器。
```

### 理论溯源

```text
$halliday-sfl-analyst

语法隐喻最早是什么时候提出的？请区分概念先声、术语的早期出现、成熟现象的明确命名
和经典系统阐述；优先引用一手来源，并写明完整书名／论文名和核验页码。
```

### 流行语与新义

```text
$halliday-sfl-analyst

从语法隐喻角度分析“游客纷纷来这里打卡”中的“打卡”。先分别查询《现代汉语词典》
第7版和侯敏《汉语新词语词典（2000—2020）》；如果语境义仍未覆盖，再核验在线新词语库。
给出词条定位、自然汉语一致式、最强反分析和页码经过核验的理论来源。
```

## 识别方法

插件不会仅凭词缀或名词化外形下判断，而是沿着可审计证据链工作：

```text
语境与言语功能 → 意义及系统选择 → 一致式候选
→ 语义层与词汇语法层映射比较 → 明确重映射＋排除纯词汇隐喻
→ 具名扩展框架下的可选操作检验 → 最强反证
→ 概念／人际独立判定＋置信度＋复核
→ 完整且页码经过核验的理论来源
```

核心判据遵循 Halliday：语法隐喻必须表现为语义类别与词汇语法实现之间的重新映射，并有合理的一致式关系项。名词、名词化、级转移、词汇隐喻或模型概率都不能单独证明 GM。Wen Li 与杨炳钧提出的 MPP／语义交汇／级阶诊断，以及杨炳钧提出的 FRP、Context-first 和 AS IF，是后续操作化工具，只在明确标记的扩展 profile 下使用，不能取代 Halliday 的核心判据。

机器判定遵守：

```text
gm_candidate = mapping_mismatch
               AND congruent_agnate_plausible
               AND remapping_explicit
               AND NOT lexical_only
```

孤立词语境不足时，概念与人际两轴都必须是 `INDETERMINATE`，置信度为 `LOW`，并进入人工复核；条件性解读只能保留为候选，不能成为确定标签。

## 可复现的 Schema v3 语法隐喻标注

只有 **annotate** 模式中的正式记录，以及 research 中明确要求逐项编码的记录，才输出固定 JSON。Schema v3 分别记录概念和人际状态，极性作为可共现维度另行记录，并包含候选跨度、一致式、跨层映射、重映射、排除项、正证、反证、置信度、分析器版本、来源和人工复核状态。

汉语 MPP 使用语言内部的审慎排序，不伪造英语式派生关系；只要运行汉语 MPP，就必须标记跨语言谨慎并人工复核。无依赖校验器支持单个 JSON、JSON 数组、JSONL／NDJSON 和 CSV：

```bash
python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/validate_gm_annotation.py \
  annotation.json
```

Schema v2 只保留用于兼容旧记录；新标注必须使用 v3。

## 汉语分析不是英语框架的机械移植

[独立汉语分析框架](plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/references/chinese-sfl-analysis.md)涵盖汉语过程类型、主位、语气与情态、小句复合体、零派生、概念功能转移候选和汉语语气／情态隐喻。

它要求给出自然的汉语一致式，不会把 `的`、句末语气词、`是……的`、`有……`、`我想／我认为／我觉得……` 自动当成隐喻标记。

## 流行语的词典证据链

[词汇证据协议](plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/references/lexical-evidence.md)要求先固定语境义，再判断语法隐喻：

1. 分别精确查询两部本机私有词典，保留全部同形义项和义项标记；
2. 报告每部词典的命中状态、完整书名、词条和 TXT 行号；
3. 两部词典都没有覆盖当前语境义时，再对中国传媒大学“新词语研究资源库”进行一次受限精确查询；
4. 把词典／网页提供的词义证据与 Halliday／杨炳钧判据提供的理论证据分开。

词典收录或未收录、比喻来源、普通语义扩展和词性标签都不能单独证明或排除语法隐喻。TXT 行号只按 TXT 行号报告，不能虚构成纸书页码。

公开插件只附带私有建库和在线补查代码，不附带词典全文。用户用自己合法取得的文本建立索引后，可把索引放在 `~/.codex` 用户级目录，让新任务和其他项目自动发现。

## 来源核验与隐私

理论回答必须写出**具体书名、论文名、章节名或演示文稿名**，不能只写“PDF”。定位规则是：

- 印刷页码 + 从 1 开始计的 PDF 页；
- 从 1 开始计的 PPTX 幻灯片编号；
- EPUB 无固定页码时，给出章节／小节及 href/anchor；
- 词典 TXT 无可靠纸书页码映射时，给出完整词典名称、词条和 TXT 行号。

公开仓库只包含原创分析框架、来源目录、引证协议和索引工具，不公开受版权保护的书籍、词典、演示文稿、抽取文本、本机绝对路径或私有索引。用户在本地映射自己合法取得的资料。

归档、完整性校验、建索引和页码映射方法见[私有语料库与页码核验](docs/private-corpus.md)。

## 参与改进

欢迎提交可复现的误判案例、汉语反例、来源页码修正和分析透明度改进。请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，并且不要上传受版权保护的原始资料。

## 本地验证

```bash
python3 -m unittest discover \
  -s plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/tests \
  -p 'test_*.py' -v
python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/test_lexicon_index.py
python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/test_source_archive.py
npm run test:node
python3 scripts/release_check.py
git diff --check
```

最低 Python 版本为 3.11；核心分析与 Schema 校验只使用标准库。PDF 语料建索引是可选功能，可运行 `python3 -m pip install '.[pdf-index]'` 安装 `pypdf`。Node 20+ 只用于在线新词查询适配器及其测试。

## 等待仓库所有者确认的元数据

仓库所有者尚未选择公开许可证，也未确认 `CITATION.cff` 所需的作者身份／ORCID。在加入 `LICENSE` 前，仓库本身不授予复用许可。CI 会报告这两个缺项，但不会擅自填入许可证、作者或发布标签。
