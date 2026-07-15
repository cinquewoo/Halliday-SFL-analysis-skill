# Halliday corpus catalog

This catalog defines stable source IDs for the reference corpus originally used to develop the skill. The PDFs are not bundled or redistributed. Resolve each ID against user-supplied or legally available local files and verify the edition before citing it.

| Source ID | Work | Reference file pages | Notes |
| --- | --- | ---: | --- |
| `ifg4` | Halliday & Matthiessen, *Halliday's Introduction to Functional Grammar*, 4th ed. | 808 | Primary grammar reference; encoded PDF page labels are available. |
| `continuum-companion` | Halliday & Webster, eds., *Continuum Companion to Systemic Functional Linguistics* | 308 | Secondary/companion source; label as secondary unless citing Halliday's own contribution. |
| `construing-experience-zh-ocr` | Halliday & Matthiessen, *Construing Experience through Meaning*, Chinese OCR edition | 693 | OCR is noisy; cross-check terminology and quotations against an English source when possible. |
| `cw1-grammar` | *Collected Works of M. A. K. Halliday*, vol. 1, *On Grammar* | 453 | Primary collected papers. |
| `cw2-text-discourse` | Vol. 2, *Linguistic Studies of Text and Discourse* | 316 | Primary collected papers. |
| `cw3-language-linguistics` | Vol. 3, *On Language and Linguistics* | 489 | Primary collected papers. |
| `cw4-early-childhood` | Vol. 4, *The Language of Early Childhood* | 430 | Primary collected papers. |
| `cw5-science` | Vol. 5, *The Language of Science* | 268 | Primary collected papers. |
| `cw6-computational` | Vol. 6, *Computational and Quantitative Studies* | 311 | Primary collected papers. |
| `cw7-english` | Vol. 7, *Studies in English Language* | 388 | Primary collected papers. |
| `cw8-chinese` | Vol. 8, *Studies in Chinese Language* | 395 | Primary collected papers. |
| `cw9-education` | Vol. 9, *Language and Education* | 417 | Primary collected papers. |
| `cw10-society` | Vol. 10, *Language and Society* | 328 | Primary collected papers. |
| `cw11-21c` | Vol. 11, *Halliday in the 21st Century* | 270 | Primary collected papers. |
| `cw11-preview` | *Halliday in the 21st Century*, separately supplied pp. 1-100 PDF excerpt | 100 | Partial duplicate; identify as an excerpt and prefer the full volume for final citations. |
| `complementarities-ocr` | Halliday, *Complementarities in Language*, OCR edition | 243 | OCR edition; verify wording and printed pagination visually when necessary. |

## Local resolution

Look for `.agents/halliday-corpus.local.json` in the active workspace. Its `sources` array maps these IDs to local PDF paths. If no manifest is present, resolve files explicitly mentioned or attached by the user. Do not assume that a same-titled PDF has the same pagination: compare title, edition, page count, and page labels first.

Use this minimal manifest shape and keep the file private:

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

Use `scripts/corpus_index.py` to build or query a local full-text index. The index stores extracted page text for private local retrieval and must not be committed or redistributed.

## Topic routing

Use these routes only to select candidate sources; always verify the actual page before citing it.

- Grammar architecture, metafunction, rank, stratification, instantiation: `ifg4`, `cw1-grammar`, `cw3-language-linguistics`.
- Transitivity, Mood, Theme, clause systems: `ifg4`, `cw1-grammar`, `cw7-english`.
- Text, cohesion, discourse, texture: `cw2-text-discourse`, `ifg4`.
- Register, context, social semiotic, language and society: `cw10-society`, `cw3-language-linguistics`.
- Child language, ontogenesis, learning language: `cw4-early-childhood`, `cw9-education`.
- Scientific discourse and grammatical metaphor: `cw5-science`, `construing-experience-zh-ocr`, `ifg4`.
- Probability, corpus, computation, quantitative modelling: `cw6-computational`, `cw11-21c`.
- Chinese language: `cw8-chinese`; use language-specific categories rather than transferring English analyses mechanically.
- Appliable linguistics and late theoretical synthesis: `cw11-21c`, `cw3-language-linguistics`.
