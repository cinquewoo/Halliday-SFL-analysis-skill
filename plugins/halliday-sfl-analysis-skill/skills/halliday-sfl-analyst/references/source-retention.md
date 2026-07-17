# Private source retention and integrity

Use this reference when the user supplies PDFs or PPTX files, asks to preserve the evidence corpus, or needs the local index rebuilt.

## Retention contract

1. Preserve each supplied source as an immutable, content-addressed local copy.
2. Record its stable source ID, full title, original filename, file type, byte size, SHA-256 digest, archive path, and archive timestamp in a private manifest.
3. Keep source binaries, absolute local paths, extracted page text, and SQLite indexes out of the public plugin repository unless the rights holder has explicitly authorized redistribution.
4. Publish only the plugin code, source catalog, bibliographic metadata, and citation workflow by default.
5. Re-run integrity verification after archiving and before relying on an archived file whose provenance is in doubt.

Use `scripts/source_archive.py`:

```bash
python3 scripts/source_archive.py archive \
  --manifest .agents/halliday-corpus.local.json \
  --destination ~/.codex/halliday-sfl-analysis-sources \
  --output-manifest .agents/halliday-corpus.archived.local.json

python3 scripts/source_archive.py verify \
  --manifest .agents/halliday-corpus.archived.local.json
```

The archive command uses an APFS clone when available and otherwise makes a byte-for-byte copy. Existing content with the same SHA-256 digest is reused. A changed source creates a new version instead of overwriting the earlier copy.

## Supported evidence files

- PDF: index by one-based PDF page; retain encoded or visually verified printed page labels separately.
- PPTX: index visible slide text and speaker notes by one-based slide number.

Build the searchable private index from the archived manifest, not from files in a transient upload directory:

```bash
python3 scripts/corpus_index.py build \
  --manifest .agents/halliday-corpus.archived.local.json \
  --database .agents/cache/halliday-corpus.sqlite3
```

The index is a locator, not final evidence. Open the complete PDF page or PPTX slide and inspect its context before citation. Render or visually inspect slides containing diagrams, screenshots, tables, or uncertain OCR.

## Portability

An installed user does not receive copyrighted source binaries. They can map stable IDs from `corpus-catalog.md` to legally available local copies, archive them, and rebuild the index. If a requested source is unavailable, state `source unavailable for page verification`; do not fabricate a page, slide, quotation, or bibliographic detail.
