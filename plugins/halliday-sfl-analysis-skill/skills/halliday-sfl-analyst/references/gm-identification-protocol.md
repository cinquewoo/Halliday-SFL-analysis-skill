# Legacy route: GM instance identification

This filename remains for backward compatibility. The active instance workflow is
[gm-decision-protocol.md](gm-decision-protocol.md).

Important migration changes:

- ordinary GM instance questions use **explain** mode and no longer require a full
  JSON object;
- JSON, Schema, coding, annotation, or batch requests use **annotate** mode and
  [gm-annotation-schema.md](gm-annotation-schema.md);
- corpus design, evaluation, provenance, and statistics use **research** mode; only
  formal item-level coding uses v3 records, and every formal record is validated;
- insufficient context now forces both GM axes to `INDETERMINATE`, confidence to
  `LOW`, and human review to `true`;
- a conditional reading is a candidate interpretation, not a definitive label.

For theory and source lineage, use [gm-theory.md](gm-theory.md). Do not infer GM from
a noun, nominal morphology, lexical metaphor, embedding, rank shift, or model score.
