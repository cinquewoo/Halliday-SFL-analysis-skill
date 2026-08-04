# Contributing

Thanks for helping make Halliday SFL Analyst more accurate, transparent, and useful.

## Good contributions

- reproducible false positives or false negatives in SFL or grammatical-metaphor analysis;
- Chinese examples that expose an English-to-Chinese transfer error;
- corrections to bibliographic identities, page labels, or source locations;
- clearer counter-tests, congruent agnates, or confidence rules;
- improvements to installation, validation, and documentation.

For an analysis issue, include the exact input, intended context, observed result, expected result, and the smallest source-backed reason the current result should change. Remove confidential text and use a short constructed example when possible.

## Before opening a pull request

1. Keep the change focused and explain the analytical consequence.
2. Update the relevant reference file as well as `SKILL.md` when behavior changes.
3. Verify every theoretical citation against the complete source unit.
4. Add or update a constructed gold case and regression test for behavioral changes.
5. Run the Python/Node tests and `python3 scripts/release_check.py` shown in the README.
6. Run `git diff --check` and confirm that no private corpus paths or source files are included.

## Source and copyright policy

Do not upload copyrighted books, articles, presentations, extracted source text, private indexes, or absolute local paths. A contribution may add original distillation and bibliographic metadata, with short quotations only where legally appropriate.

The repository's public license is awaiting owner confirmation. Do not assume an
open-source license from public visibility alone. By submitting a contribution, you
confirm that you have the right to provide it and understand that acceptance remains
subject to the license terms the owner later selects.
