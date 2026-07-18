# Private corpus and page verification

The plugin can archive and index a user's legally available PDF, PPTX, and EPUB sources without committing those source binaries or extracted text to the public repository.

## 1. Map stable source IDs to local files

Create `.agents/halliday-corpus.local.json` locally. It is ignored by Git.

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
      "page_label_mode": "encoded",
      "path": "/absolute/path/to/IFG4.pdf"
    }
  ]
}
```

Stable source IDs and their bibliographic identities are defined in `references/corpus-catalog.md` inside the skill.

## 2. Archive originals and verify integrity

The archiver uses APFS cloning when available and otherwise makes a byte-for-byte copy. It records SHA-256 integrity metadata.

```bash
python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/source_archive.py \
  archive --manifest .agents/halliday-corpus.local.json \
  --destination ~/.codex/halliday-sfl-analysis-sources \
  --output-manifest .agents/halliday-corpus.archived.local.json

python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/source_archive.py \
  verify --manifest .agents/halliday-corpus.archived.local.json
```

## 3. Build the private index

```bash
python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/corpus_index.py \
  build --manifest .agents/halliday-corpus.archived.local.json \
  --database .agents/cache/halliday-corpus.sqlite3
```

The indexer requires Python and `pypdf`. PPTX and EPUB text extraction uses the Python standard library.

## 4. Search, then inspect the complete evidence unit

```bash
python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/corpus_index.py \
  search --database .agents/cache/halliday-corpus.sqlite3 \
  --source ifg4 --query "resource making meaning"

python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/corpus_index.py \
  page --database .agents/cache/halliday-corpus.sqlite3 \
  --source ifg4 --pdf-page 22

python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/corpus_index.py \
  page --database .agents/cache/halliday-corpus.sqlite3 \
  --source gm-improvements-2026 --slide 103

python3 plugins/halliday-sfl-analysis-skill/skills/halliday-sfl-analyst/scripts/corpus_index.py \
  page --database .agents/cache/halliday-corpus.sqlite3 \
  --source yang-yanning-2020-chinese-gm --epub-unit 19
```

Search hits are candidate evidence, not citations by themselves. Inspect the full page, slide, or EPUB section and visually check scans, OCR, screenshots, tables, diagrams, and uncertain page labels before citing.

## 5. Handle unreliable PDF page labels

- Use `"page_label_mode": "encoded"` only when embedded labels are trustworthy.
- For a stable offset, use `"page_label_mode": "offset"` with visually verified `printed_page_start` and `printed_page_pdf_start`.
- Use `"page_label_mode": "none"` when no reliable printed-page mapping exists.

The index never treats a publisher's article number as a page number merely because it appears in `/PageLabels`.

## Public/private boundary

Do not commit source binaries, extracted text, absolute local paths, private manifests, or SQLite indexes. The repository's `.gitignore` excludes the standard private manifests and index directory.
