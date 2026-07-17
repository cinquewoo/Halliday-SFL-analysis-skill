# Source and page citation protocol

Use this protocol for every answer that explains Hallidayan theory, defines an SFL term, attributes a position, summarizes the SFL corpus, or grounds a textual analysis in theory. A locator without a complete source identity is not a citation.

## Mandatory answer contract

Every theory-bearing answer must include a compact `Sources` or `Theoretical sources` section. Each entry must identify the source before giving a page or slide:

- **Book:** author(s), year, complete book title, edition, chapter/section, printed page, and one-based PDF page.
- **Collected article/chapter:** author, original year, article/chapter title, editor when known, complete containing book title and volume, printed page, and one-based PDF page.
- **Journal article:** author(s), year, article title, complete journal title, volume(issue), printed page range or supporting page, and PDF page when a local file is used.
- **Presentation:** presenter, year/date, complete presentation title, venue/event, and one-based PPTX slide number.

Never write only `PDF p. 22`, `slide 45`, a filename, a source ID, an abbreviated title such as `IFG`, or a volume number. Short forms may appear in the discussion only after the complete source has been supplied in the same answer.

## Evidence hierarchy

Prefer evidence in this order:

1. The exact Halliday or Halliday-and-Matthiessen primary text supplied by the user.
2. Another primary text in Halliday's collected works that states the same point.
3. An edited companion or later SFL source, explicitly labelled as secondary.
4. The bundled theoretical distillation, used only to locate likely primary sources.

Never present the distillation or model memory as if it were a page-verified primary source.

## Required verification workflow

1. Identify the proposition that needs support. Split compound theoretical claims when one source does not support every part.
2. Search the available corpus by distinctive English terms and plausible variants. For translated or OCR sources, also search the corresponding English term.
3. Open the complete PDF page or PPTX slide containing the hit. Read enough surrounding text or adjacent slides to establish the author's claim and avoid citing a table of contents, index, bibliography, screenshot, or quoted opponent as the source author's own position.
4. Record the stable source ID, complete bibliographic or presentation identity, chapter/article/section when available, and the applicable locator.
5. Check the original visually when extraction is garbled, the scan crops a footer, a table or diagram carries the evidence, a slide contains screenshots, or the printed page number is uncertain.
6. Cite the narrowest page span that supports the claim. Do not cite a whole book or broad chapter when a precise page is available.
7. If the exact locator cannot be verified, say so and either give a section-level locator marked `page/slide unverified` or withhold the attribution. Never invent or infer a page number from an offset.
8. Confirm source-file integrity against the archived SHA-256 manifest when provenance or file identity is uncertain.

## Page-number policy

- Prefer the page number printed in the book or encoded as the PDF page label.
- Also give the one-based PDF page number so the user can navigate the supplied file.
- Format a single page as `printed p. 3; PDF p. 22`.
- Format a span as `printed pp. 3-5; PDF pp. 22-24`.
- If the PDF has no reliable printed label, use `printed page unavailable; PDF p. 30`.
- For Roman-numbered front matter, preserve the label: `printed p. xv; PDF p. 16`.
- For OCR editions, append `OCR edition` and verify ambiguous wording against a clean English edition when possible.
- Treat a separately supplied partial PDF as a different file. Cite its own PDF page and identify it as an excerpt; do not silently substitute its page number for the full volume.

PDF page numbers in this protocol are one-based: the first page displayed by the PDF reader is PDF p. 1.

For PPTX files:

- Count the first slide as `PPTX slide 1`.
- Cite a single slide as `PPTX slide 103` and a span as `PPTX slides 103-107`.
- If the deck was also exported to PDF, identify the exported file separately; do not substitute its PDF page silently for the PPTX slide number.
- Treat an AI answer screenshot or quotation shown on a slide as evidence being discussed, not automatically as the presenter's endorsed claim.

## Citation formats

Use a compact inline form for ordinary answers:

> Halliday, M. A. K., and Christian M. I. M. Matthiessen. 2014. *Halliday's Introduction to Functional Grammar*, 4th ed., Ch. 1, `1.1 Text and grammar` (printed p. 3; PDF p. 22).

For an article in the collected works:

> Halliday, M. A. K. 2003. `On the architecture of human language`, in Jonathan J. Webster (ed.), *On Language and Linguistics: Volume 3 in the Collected Works of M. A. K. Halliday* (printed pp. 1-3; PDF pp. 18-20).

For a secondary source:

> Secondary account: Halliday, M. A. K., and Jonathan J. Webster (eds.). 2009. *Continuum Companion to Systemic Functional Linguistics*, chapter title (printed p. x; PDF p. y).

For a presentation:

> Yang, Bingjun. 2026. *Grammatical Metaphor: Improvements and Applications*. Presentation at the 51st International Systemic Functional Congress, Hong Kong Metropolitan University, 11 July 2026 (PPTX slides 103-107).

When the answer contains several claims, add a short `Sources` list mapping each source to the proposition it supports. Do not repeat the same full citation after every sentence when one clearly scoped paragraph and one citation suffice.

## Separate three kinds of evidence

- **Corpus evidence**: wording and verified page/slide locations in identified primary or secondary sources.
- **Text evidence**: clauses, paragraphs, counts, or page locations in the user's analyzed text.
- **Analyst inference**: the functional interpretation made from those two evidence sets.

Label synthesis and inference as interpretation rather than attributing them directly to Halliday. For a synthesis across works, cite at least two primary locations unless one passage explicitly makes the synthesis.

## Quotations and paraphrases

- Quote only the minimum wording required to establish the point.
- Preserve the source language and supply a clearly marked translation only when useful.
- Put OCR repairs in square brackets or state that punctuation/spacing was normalized.
- For paraphrases, keep the citation and do not use quotation marks.
- Do not attribute later Appraisal, multimodality, genre, or corpus developments to Halliday without identifying the later author or tradition.

## Failure labels

Use one of these labels instead of bluffing:

- `Page verified`: source page and surrounding context were checked.
- `Slide verified`: source slide, adjacent context, and relevant visual content were checked.
- `Section located, page unverified`: the section is known but pagination was not confirmed.
- `Presentation located, slide unverified`: the presentation is known but the slide was not confirmed.
- `Source unavailable for page verification`: a bibliographic lead exists but the original file is inaccessible.
- `Secondary source only`: no primary passage has yet been verified.
- `Analytical inference`: the statement is the analyst's application of SFL categories.
