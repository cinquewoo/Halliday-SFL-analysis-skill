# Legacy route: grammatical-metaphor annotation v2

Schema v2 remains readable for existing datasets, but new annotations use
[gm-annotation-schema.md](gm-annotation-schema.md) and
[gm-annotation-v3.schema.json](gm-annotation-v3.schema.json).

The unified validator accepts both versions:

```bash
python3 scripts/validate_gm_annotation.py annotation.json
```

Every formal v2 or v3 record must pass this validator before it is returned, saved,
or shared.

Unversioned records shaped like the former 41-field contract are treated as v2;
`schema_version="3.0"` selects v3. The conservative context gate is applied to both.
Validation never silently migrates a record.

V2's MPP, FRP, rank, and semantic-junction fields represented a specific later
operational profile. They must not be described as Halliday's original terminology
or as substitutes for semantic–lexicogrammatical re-mapping. See
[gm-theory.md](gm-theory.md) and
[gm-decision-protocol.md](gm-decision-protocol.md).
