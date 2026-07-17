# Halliday corpus catalog

This catalog defines stable source IDs and complete source titles for the reference corpus used to develop the skill. The user's originals are retained in a private content-addressed archive; copyrighted PDF/PPTX binaries are not bundled in the public plugin. Resolve each ID against a legally available local file and verify the edition before citing it.

| Source ID | Work | Reference file pages | Notes |
| --- | --- | ---: | --- |
| `ifg4` | M. A. K. Halliday & Christian M. I. M. Matthiessen, *Halliday's Introduction to Functional Grammar*, 4th ed. | 808 | Primary grammar reference; encoded PDF page labels are available. |
| `continuum-companion` | M. A. K. Halliday & Jonathan J. Webster, eds., *Continuum Companion to Systemic Functional Linguistics* | 308 | Secondary/companion source; label as secondary unless citing Halliday's own contribution. |
| `construing-experience-zh-ocr` | M. A. K. Halliday & Christian M. I. M. Matthiessen, *Construing Experience through Meaning: A Language-based Approach to Cognition*, Chinese OCR edition | 693 | OCR is noisy; cross-check terminology and quotations against an English source when possible. |
| `cw1-grammar` | Jonathan J. Webster, ed., *On Grammar: Volume 1 in the Collected Works of M. A. K. Halliday* | 453 | Primary collected papers. |
| `cw2-text-discourse` | Jonathan J. Webster, ed., *Linguistic Studies of Text and Discourse: Volume 2 in the Collected Works of M. A. K. Halliday* | 316 | Primary collected papers. |
| `cw3-language-linguistics` | Jonathan J. Webster, ed., *On Language and Linguistics: Volume 3 in the Collected Works of M. A. K. Halliday* | 489 | Primary collected papers. |
| `cw4-early-childhood` | Jonathan J. Webster, ed., *The Language of Early Childhood: Volume 4 in the Collected Works of M. A. K. Halliday* | 430 | Primary collected papers. |
| `cw5-science` | Jonathan J. Webster, ed., *The Language of Science: Volume 5 in the Collected Works of M. A. K. Halliday* | 268 | Primary collected papers. |
| `cw6-computational` | Jonathan J. Webster, ed., *Computational and Quantitative Studies: Volume 6 in the Collected Works of M. A. K. Halliday* | 311 | Primary collected papers. |
| `cw7-english` | Jonathan J. Webster, ed., *Studies in English Language: Volume 7 in the Collected Works of M. A. K. Halliday* | 388 | Primary collected papers. |
| `cw8-chinese` | Jonathan J. Webster, ed., *Studies in Chinese Language: Volume 8 in the Collected Works of M. A. K. Halliday* | 395 | Primary collected papers. |
| `cw9-education` | Jonathan J. Webster, ed., *Language and Education: Volume 9 in the Collected Works of M. A. K. Halliday* | 417 | Primary collected papers. |
| `cw10-society` | Jonathan J. Webster, ed., *Language and Society: Volume 10 in the Collected Works of M. A. K. Halliday* | 328 | Primary collected papers. |
| `cw11-21c` | Jonathan J. Webster, ed., *Halliday in the 21st Century: Volume 11 in the Collected Works of M. A. K. Halliday* | 270 | Primary collected papers. |
| `cw11-preview` | *Halliday in the 21st Century: Volume 11 in the Collected Works of M. A. K. Halliday*, separately supplied 100-page excerpt | 100 | Partial duplicate; identify as an excerpt and prefer the full volume for final citations. |
| `complementarities-ocr` | M. A. K. Halliday, *Complementarities in Language* (《语言系统的并协与互补》), OCR edition | 243 | OCR edition; verify wording and printed pagination visually when necessary. |
| `gm-improvements-2026` | Bingjun Yang, *Grammatical Metaphor: Improvements and Applications*, ISFC 51 presentation, Hong Kong Metropolitan University, 11 July 2026 | 208 slides | Secondary research presentation; distinguish Yang's refinements from screenshots and cited authors. |
| `li-yang-2024-nominalizing-metaphors` | Wen Li & Bingjun Yang, `Towards a system of principles for identifying nominalizing metaphors`, *Lingua* 312: 103832 | 21 | Four-system NM identification: semantic junction, morphological priority, full realization, and rank shift. |
| `yang-gao-2023-polarity-metaphor` | Bingjun Yang & Hongmiao Gao, `Polarity metaphor in English: Definition, identification, and categorization`, *Lingua* 295: 103623 | 16 | Ideational and interpersonal polarity metaphor; direct negative agnates and polarity cline. |
| `yang-2019-interpersonal-metaphor` | Bingjun Yang, `Interpersonal metaphor revisited: identification, categorization, and syndrome`, *Social Semiotics* 29(2): 186-203 | 19 | Context-first and AS IF principles; PDF p. 2 corresponds to printed p. 186. |
| `yang-2018-textual-metaphor` | Bingjun Yang, `Textual Metaphor Revisited`, *Australian Journal of Linguistics* 38(2): 205-222 | 19 | Critical account of textual-GM identification; PDF p. 2 corresponds to printed p. 205. |
| `yang-2020-full-realization` | Bingjun Yang, `Full realization principle for the identification of ideational grammatical metaphor: nominalization as example`, *Journal of World Languages* 6(3): 161-174 | 14 | Full/intermediate/raw realization and embedding counter-test; PDF p. 1 corresponds to printed p. 161. |

## Local resolution

Prefer `.agents/halliday-corpus.archived.local.json`; otherwise look for `.agents/halliday-corpus.local.json`. Their `sources` arrays map stable IDs to private PDF/PPTX paths. If no manifest is present, resolve files explicitly supplied by the user. Do not assume that a same-titled file has the same pagination: compare title, edition, page/slide count, labels, and SHA-256 digest first.

Use this minimal manifest shape and keep the file private:

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
      "path": "/absolute/path/to/IFG4.pdf",
      "sha256": "verified-file-digest"
    }
  ]
}
```

`page_label_mode` may be `encoded` (default), `offset`, or `none`. Use `offset` only after visually verifying a stable mapping and add positive integers `printed_page_start` and `printed_page_pdf_start`. Use `none` when neither embedded labels nor a visually verified mapping is reliable. The index reports the original presence of encoded labels separately from the selected locator mode.

Use `scripts/source_archive.py` to retain originals privately and create SHA-256 metadata. Then use `scripts/corpus_index.py` to build or query a page/slide index. The archive, manifest, extracted text, and SQLite database must remain private unless redistribution rights are established.

## Topic routing

Use these routes only to select candidate sources; always verify the actual page before citing it.

- Grammar architecture, metafunction, rank, stratification, instantiation: `ifg4`, `cw1-grammar`, `cw3-language-linguistics`.
- Transitivity, Mood, Theme, clause systems: `ifg4`, `cw1-grammar`, `cw7-english`.
- Text, cohesion, discourse, texture: `cw2-text-discourse`, `ifg4`.
- Register, context, social semiotic, language and society: `cw10-society`, `cw3-language-linguistics`.
- Child language, ontogenesis, learning language: `cw4-early-childhood`, `cw9-education`.
- Scientific discourse and grammatical metaphor: `cw5-science`, `construing-experience-zh-ocr`, `ifg4`.
- Grammatical-metaphor history and applications: `gm-improvements-2026`, then verify any Halliday attribution in the primary volume it names.
- Nominalizing-metaphor instance identification: `li-yang-2024-nominalizing-metaphors`, `yang-2020-full-realization`, then `ifg4` for Halliday's re-mapping account.
- Mood or modality metaphor identification: `yang-2019-interpersonal-metaphor`, then `ifg4` and the Halliday source relevant to the example.
- Polarity metaphor: `yang-gao-2023-polarity-metaphor`, `cw8-chinese`, and `ifg4`.
- Proposed textual metaphor: `yang-2018-textual-metaphor`, `cw2-text-discourse`, and `ifg4`; report the category's contested status.
- Probability, corpus, computation, quantitative modelling: `cw6-computational`, `cw11-21c`.
- Chinese language: `cw8-chinese`; use language-specific categories rather than transferring English analyses mechanically.
- Appliable linguistics and late theoretical synthesis: `cw11-21c`, `cw3-language-linguistics`.
