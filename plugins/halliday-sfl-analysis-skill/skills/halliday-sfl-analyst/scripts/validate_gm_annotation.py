#!/usr/bin/env python3
"""Validate Halliday SFL grammatical-metaphor annotation v2 JSON records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SCHEMA = SCRIPT_DIR.parent / "references" / "gm-annotation-v2.schema.json"
NOMINALIZING_TYPES = {
    "NOM_QUALITY",
    "NOM_PROCESS",
    "NOM_CIRCUMSTANCE",
    "NOM_RELATOR",
}
MOOD_TYPES = {"MOOD_METAPHOR", "MOOD_AND_MODALITY"}
MODALITY_TYPES = {"MODALITY_METAPHOR", "MOOD_AND_MODALITY"}
REVIEW_STATUSES = {"MARGINAL_GM", "INDETERMINATE"}


def type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def resolve_ref(schema: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    ref = spec.get("$ref")
    if not ref:
        return spec
    prefix = "#/$defs/"
    if not ref.startswith(prefix):
        raise ValueError(f"unsupported schema reference: {ref}")
    return schema["$defs"][ref.removeprefix(prefix)]


def validate_shape(record: Any, schema: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return [f"{label}: expected an object"]

    required = set(schema.get("required", []))
    properties = schema.get("properties", {})
    missing = sorted(required - record.keys())
    extra = sorted(record.keys() - properties.keys())
    if missing:
        errors.append(f"{label}: missing fields: {', '.join(missing)}")
    if extra and schema.get("additionalProperties") is False:
        errors.append(f"{label}: unexpected fields: {', '.join(extra)}")

    for key, value in record.items():
        if key not in properties:
            continue
        spec = resolve_ref(schema, properties[key])
        expected = spec.get("type")
        if expected is not None:
            accepted = [expected] if isinstance(expected, str) else expected
            if not any(type_matches(value, item) for item in accepted):
                errors.append(
                    f"{label}.{key}: expected {' or '.join(accepted)}, "
                    f"got {type(value).__name__}"
                )
                continue
        if "enum" in spec and value not in spec["enum"]:
            errors.append(f"{label}.{key}: invalid enum value {value!r}")
        if isinstance(value, str) and len(value) < spec.get("minLength", 0):
            errors.append(f"{label}.{key}: string is shorter than minLength")
        if isinstance(value, list):
            item_spec = spec.get("items", {})
            for index, item in enumerate(value):
                item_type = item_spec.get("type")
                if item_type and not type_matches(item, item_type):
                    errors.append(
                        f"{label}.{key}[{index}]: expected {item_type}, "
                        f"got {type(item).__name__}"
                    )
                if (
                    isinstance(item, str)
                    and len(item) < item_spec.get("minLength", 0)
                ):
                    errors.append(f"{label}.{key}[{index}]: empty string is not allowed")
    return errors


def validate_cross_fields(record: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []

    def error(message: str) -> None:
        errors.append(f"{label}: {message}")

    ideational_status = record.get("ideational_gm_status")
    interpersonal_status = record.get("interpersonal_gm_status")
    ideational_type = record.get("ideational_type")
    interpersonal_type = record.get("interpersonal_type")
    mpp_status = record.get("mpp_status")
    mpp_applicability = record.get("mpp_applicability")

    if not record.get("evidence"):
        error("evidence must contain at least one explicit observation")
    if not record.get("counterevidence"):
        error("counterevidence must contain the strongest contrary analysis")

    if mpp_applicability == "APPLICABLE":
        if not record.get("mpp_candidate_agnates"):
            error("applicable MPP requires at least one candidate agnate")
        if mpp_status == "NOT_APPLICABLE":
            error("mpp_status cannot be NOT_APPLICABLE when MPP is applicable")
    if mpp_applicability == "NOT_APPLICABLE":
        if mpp_status != "NOT_APPLICABLE":
            error("non-applicable MPP requires mpp_status=NOT_APPLICABLE")
        if record.get("mpp_agnation_level") != "NOT_APPLICABLE":
            error("non-applicable MPP requires mpp_agnation_level=NOT_APPLICABLE")
        if record.get("mpp_candidate_agnates"):
            error("non-applicable MPP cannot contain candidate agnates")
        if record.get("mpp_selected_agnate") is not None:
            error("non-applicable MPP cannot contain a selected agnate")
    if mpp_applicability == "UNCLEAR" and mpp_status != "UNCLEAR":
        error("unclear MPP applicability requires mpp_status=UNCLEAR")
    if mpp_status in {"PASS", "FAIL"} and mpp_applicability != "APPLICABLE":
        error(f"MPP {mpp_status} requires mpp_applicability=APPLICABLE")
    if mpp_status == "PASS" and not record.get("mpp_selected_agnate"):
        error("MPP PASS requires mpp_selected_agnate")
    if mpp_status == "PASS" and record.get("mpp_higher_priority_available"):
        error("MPP cannot PASS while a higher-priority agnate is available")
    if mpp_status == "FAIL" and not record.get("mpp_violation_reason"):
        error("MPP FAIL requires mpp_violation_reason")
    if mpp_status == "FAIL" and ideational_status == "TYPICAL_GM":
        error("MPP FAIL cannot receive TYPICAL_GM")

    if ideational_type in NOMINALIZING_TYPES and mpp_applicability == "NOT_APPLICABLE":
        error("a nominalizing candidate must run MPP")

    if ideational_status == "TYPICAL_GM" and ideational_type in NOMINALIZING_TYPES:
        expected = {
            "congruent_agnate": lambda value: isinstance(value, str) and bool(value),
            "mpp_applicability": lambda value: value == "APPLICABLE",
            "mpp_status": lambda value: value == "PASS",
            "frp_realization": lambda value: value == "FULL",
            "rank_shift": lambda value: value not in {None, "NONE"},
            "semantic_junction": lambda value: value not in {None, "NONE"},
            "exclusion_reason": lambda value: value == "NONE",
        }
        for field, predicate in expected.items():
            if not predicate(record.get(field)):
                error(f"typical nominalizing GM failed gate: {field}")

    if ideational_status == "TYPICAL_GM" and record.get("confidence") == "LOW":
        error("LOW confidence cannot support an unqualified TYPICAL_GM")
    if ideational_status == "TYPICAL_GM" and ideational_type == "NONE":
        error("ideational TYPICAL_GM requires an ideational type")
    if ideational_status == "TYPICAL_GM" and record.get("exclusion_reason") != "NONE":
        error("TYPICAL_GM cannot carry an exclusion reason")

    if record.get("language") == "zh" and mpp_applicability != "NOT_APPLICABLE":
        if record.get("mpp_crosslinguistic_caution") is not True:
            error("Chinese MPP requires mpp_crosslinguistic_caution=true")
        if record.get("needs_human_review") is not True:
            error("Chinese MPP requires needs_human_review=true")
    if record.get("language") == "zh" and mpp_applicability == "APPLICABLE":
        if not str(record.get("mpp_agnation_level", "")).startswith("ZH_"):
            error("Chinese MPP requires a ZH_* agnation level")
    if (
        record.get("language") == "en"
        and mpp_applicability == "APPLICABLE"
        and str(record.get("mpp_agnation_level", "")).startswith("ZH_")
    ):
        error("English MPP cannot use a ZH_* agnation level")

    if interpersonal_type in MOOD_TYPES:
        if record.get("context_sufficiency") == "INSUFFICIENT":
            error("mood metaphor requires clause/exchange context")
        if record.get("speech_function") == "UNCLEAR":
            error("mood metaphor requires a contextual speech function")
        if record.get("mood_form") == "UNCLEAR":
            error("mood metaphor requires an identified Mood form")
        if record.get("mood_mismatch") is not True:
            error("mood metaphor requires mood_mismatch=true")
        if not record.get("as_if_relation"):
            error("mood metaphor requires an AS IF relation")

    if interpersonal_type in MODALITY_TYPES:
        if record.get("modality_type") in {None, "NONE", "UNCLEAR"}:
            error("modality metaphor requires a resolved modality type")
        if record.get("explicitness") != "EXPLICIT":
            error("modality metaphor requires EXPLICIT expanded realization")
        if not record.get("congruent_modal_rewrite"):
            error("modality metaphor requires congruent_modal_rewrite")

    if interpersonal_status == "TYPICAL_GM" and interpersonal_type == "NONE":
        error("interpersonal TYPICAL_GM requires an interpersonal type")
    if interpersonal_status == "TYPICAL_GM" and record.get("confidence") == "LOW":
        error("LOW confidence cannot support an unqualified interpersonal TYPICAL_GM")

    if record.get("context_sufficiency") == "INSUFFICIENT":
        if interpersonal_status != "INDETERMINATE":
            error("insufficient context requires interpersonal INDETERMINATE")
        if record.get("needs_human_review") is not True:
            error("insufficient context requires human review")

    if (
        record.get("confidence") != "HIGH"
        or ideational_status in REVIEW_STATUSES
        or interpersonal_status in REVIEW_STATUSES
        or mpp_status == "UNCLEAR"
    ) and record.get("needs_human_review") is not True:
        error("uncertain, marginal, or indeterminate records require human review")

    if record.get("polarity_metaphor") is True:
        if record.get("polarity_subtype") == "NONE":
            error("polarity_metaphor=true requires a polarity subtype")
    elif record.get("polarity_subtype") != "NONE":
        error("polarity_subtype must be NONE when polarity_metaphor=false")

    return errors


def load_records(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return payload
    return [payload]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Halliday SFL GM annotation v2 JSON records."
    )
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()

    with args.schema.open(encoding="utf-8") as handle:
        schema = json.load(handle)

    failures = 0
    checked = 0
    for path in args.files:
        try:
            records = load_records(path)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR {path}: {exc}", file=sys.stderr)
            failures += 1
            continue

        file_errors: list[str] = []
        for index, record in enumerate(records):
            checked += 1
            label = f"{path}[{index}]" if len(records) > 1 else str(path)
            shape_errors = validate_shape(record, schema, label)
            file_errors.extend(shape_errors)
            if isinstance(record, dict) and not shape_errors:
                file_errors.extend(validate_cross_fields(record, label))

        if file_errors:
            failures += 1
            for message in file_errors:
                print(f"ERROR {message}", file=sys.stderr)
        else:
            print(f"OK {path}: {len(records)} record(s)")

    if failures:
        print(
            f"Validation failed: {failures} file(s), {checked} record(s) checked",
            file=sys.stderr,
        )
        return 1
    print(f"Validation passed: {checked} record(s) checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
