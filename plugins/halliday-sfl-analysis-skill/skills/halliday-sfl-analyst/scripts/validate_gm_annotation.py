#!/usr/bin/env python3
"""Validate Halliday SFL grammatical-metaphor annotation v2/v3 records.

The validator has no third-party dependency.  It accepts one JSON object, a
JSON array, JSONL/NDJSON, or a CSV whose array/object cells contain JSON.
Schema v3 is the default for new annotations; unversioned legacy records are
validated against the bundled v2 contract.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
REFERENCE_DIR = SCRIPT_DIR.parent / "references"
SCHEMA_PATHS = {
    "2": REFERENCE_DIR / "gm-annotation-v2.schema.json",
    "3": REFERENCE_DIR / "gm-annotation-v3.schema.json",
}
DEFAULT_SCHEMA = SCHEMA_PATHS["3"]
DEFAULT_RULES = REFERENCE_DIR / "gm-candidate-rules.yaml"
NOMINALIZING_V2_TYPES = (
    "NOM_QUALITY",
    "NOM_PROCESS",
    "NOM_CIRCUMSTANCE",
    "NOM_RELATOR",
)
NOMINALIZING_V3_REMAPPINGS = (
    "PROCESS_TO_THING",
    "FIGURE_TO_NOMINAL_GROUP",
    "QUALITY_TO_THING",
    "CIRCUMSTANCE_TO_THING",
    "LOGICAL_RELATION_TO_THING",
)
MOOD_TYPES = ("MOOD_METAPHOR", "MOOD_AND_MODALITY")
MODALITY_TYPES = ("MODALITY_METAPHOR", "MOOD_AND_MODALITY")
REVIEW_STATUSES = ("MARGINAL_GM", "INDETERMINATE")
PRIVATE_ABSOLUTE_PATH = re.compile(r"(?:/Users/|/home/|[A-Za-z]:\\Users\\)")
CSV_FIELD_LIMIT = 1_000_000


class AnnotationInputError(ValueError):
    """Raised when an annotation container cannot be read safely."""


def has_substantive_text(value: Any) -> bool:
    """Require lexical content, not whitespace, controls, punctuation, or symbols."""

    if not isinstance(value, str) or "\x00" in value:
        return False
    return any(unicodedata.category(char)[0] in ("L", "N") for char in value)


def lexical_surface(value: Any) -> str:
    """Remove punctuation/wrappers when testing whether a WORD has real co-text."""

    if not isinstance(value, str):
        return ""
    return "".join(
        char
        for char in value.casefold()
        if unicodedata.category(char)[0] in ("L", "M", "N")
    )


def has_lexical_context(value: Any) -> bool:
    """Punctuation alone does not count as linguistic co-text."""

    return bool(lexical_surface(value))


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject ambiguous JSON instead of silently keeping the last duplicate key."""

    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AnnotationInputError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ValueError(f"unsupported schema type: {expected}")


def resolve_ref(schema: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    ref = spec.get("$ref")
    if not ref:
        return spec
    prefix = "#/$defs/"
    if not ref.startswith(prefix):
        raise ValueError(f"unsupported schema reference: {ref}")
    try:
        return schema["$defs"][ref.removeprefix(prefix)]
    except KeyError as exc:
        raise ValueError(f"unresolved schema reference: {ref}") from exc


def _validate_schema_value(
    value: Any,
    spec: dict[str, Any],
    schema: dict[str, Any],
    label: str,
) -> list[str]:
    """Validate the JSON-Schema subset used by the bundled contracts."""

    spec = resolve_ref(schema, spec)
    errors: list[str] = []

    expected = spec.get("type")
    if expected is not None:
        accepted = [expected] if isinstance(expected, str) else expected
        if not any(type_matches(value, item) for item in accepted):
            return [
                f"{label}: expected {' or '.join(accepted)}, got {type(value).__name__}"
            ]

    if "const" in spec and value != spec["const"]:
        errors.append(f"{label}: expected constant value {spec['const']!r}")
    if "enum" in spec and value not in spec["enum"]:
        errors.append(f"{label}: invalid enum value {value!r}")
    if isinstance(value, str) and len(value) < spec.get("minLength", 0):
        errors.append(f"{label}: string is shorter than minLength")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in spec and value < spec["minimum"]:
            errors.append(f"{label}: value is below minimum {spec['minimum']}")

    if isinstance(value, list):
        if len(value) < spec.get("minItems", 0):
            errors.append(f"{label}: array has fewer than minItems")
        item_spec = spec.get("items")
        if isinstance(item_spec, dict):
            for index, item in enumerate(value):
                errors.extend(
                    _validate_schema_value(item, item_spec, schema, f"{label}[{index}]")
                )

    if isinstance(value, dict):
        required = set(spec.get("required", []))
        properties = spec.get("properties", {})
        missing = sorted(required - value.keys())
        if missing:
            errors.append(f"{label}: missing fields: {', '.join(missing)}")
        if spec.get("additionalProperties") is False:
            extra = sorted(value.keys() - properties.keys())
            if extra:
                errors.append(f"{label}: unexpected fields: {', '.join(extra)}")
        for key, child in value.items():
            child_spec = properties.get(key)
            if isinstance(child_spec, dict):
                errors.extend(
                    _validate_schema_value(child, child_spec, schema, f"{label}.{key}")
                )

    if "not" in spec and not _validate_schema_value(value, spec["not"], schema, label):
        errors.append(f"{label}: value matches a forbidden schema")

    for branch in spec.get("allOf", []):
        condition = branch.get("if")
        if condition is None or not _validate_schema_value(value, condition, schema, label):
            target = branch.get("then") if condition is not None else branch
            if isinstance(target, dict):
                errors.extend(_validate_schema_value(value, target, schema, label))
        elif isinstance(branch.get("else"), dict):
            errors.extend(_validate_schema_value(value, branch["else"], schema, label))
    return errors


def validate_shape(record: Any, schema: dict[str, Any], label: str) -> list[str]:
    return _validate_schema_value(record, schema, schema, label)


def _append_error(errors: list[str], label: str, message: str) -> None:
    errors.append(f"{label}: {message}")


def validate_context_gate(record: dict[str, Any], label: str) -> list[str]:
    """Enforce the same conservative gate for v2 and v3 records."""

    v3_isolated = bool(lexical_surface(record.get("candidate_span"))) and (
        lexical_surface(record.get("sentence"))
        == lexical_surface(record.get("candidate_span"))
    )
    v2_context = record.get("context")
    v2_isolated = "sentence" not in record and (
        not has_lexical_context(v2_context)
        or (
            bool(lexical_surface(record.get("text")))
            and lexical_surface(v2_context) == lexical_surface(record.get("text"))
        )
    )
    isolated_word = (
        record.get("unit_type") == "WORD"
        and (v3_isolated or v2_isolated)
        and not has_lexical_context(record.get("context_before"))
        and not has_lexical_context(record.get("context_after"))
    )
    if isolated_word and record.get("context_sufficiency") != "INSUFFICIENT":
        return [
            f"{label}: an isolated WORD without co-text requires "
            "context_sufficiency='INSUFFICIENT'"
        ]
    if record.get("context_sufficiency") != "INSUFFICIENT" and not isolated_word:
        return []
    errors: list[str] = []
    required = {
        "ideational_gm_status": "INDETERMINATE",
        "interpersonal_gm_status": "INDETERMINATE",
        "confidence": "LOW",
        "needs_human_review": True,
    }
    for field, expected in required.items():
        if record.get(field) != expected:
            _append_error(
                errors,
                label,
                f"insufficient context requires {field}={expected!r}",
            )
    if "gm_candidate" in record and record.get("gm_candidate") is not False:
        _append_error(errors, label, "insufficient context requires gm_candidate=false")
    return errors


def validate_cross_fields_v2(record: dict[str, Any], label: str) -> list[str]:
    errors = validate_context_gate(record, label)

    def error(message: str) -> None:
        _append_error(errors, label, message)

    ideational_status = record.get("ideational_gm_status")
    interpersonal_status = record.get("interpersonal_gm_status")
    ideational_type = record.get("ideational_type")
    interpersonal_type = record.get("interpersonal_type")
    mpp_status = record.get("mpp_status")
    mpp_applicability = record.get("mpp_applicability")

    if record.get("context_sufficiency") == "PARTIAL":
        if record.get("confidence") == "HIGH":
            error("partial context cannot support HIGH confidence")
        if record.get("needs_human_review") is not True:
            error("partial context requires human review")

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
    if mpp_status in ("PASS", "FAIL") and mpp_applicability != "APPLICABLE":
        error(f"MPP {mpp_status} requires mpp_applicability=APPLICABLE")
    if mpp_status == "PASS" and not record.get("mpp_selected_agnate"):
        error("MPP PASS requires mpp_selected_agnate")
    if mpp_status == "PASS" and record.get("mpp_higher_priority_available"):
        error("MPP cannot PASS while a higher-priority agnate is available")
    if mpp_status == "FAIL" and not record.get("mpp_violation_reason"):
        error("MPP FAIL requires mpp_violation_reason")
    if mpp_status == "FAIL" and ideational_status == "TYPICAL_GM":
        error("MPP FAIL cannot receive TYPICAL_GM")

    if ideational_type in NOMINALIZING_V2_TYPES and mpp_applicability == "NOT_APPLICABLE":
        error("a nominalizing candidate must run MPP")

    if ideational_status == "TYPICAL_GM" and ideational_type in NOMINALIZING_V2_TYPES:
        expected = {
            "congruent_agnate": lambda value: isinstance(value, str) and bool(value),
            "mpp_applicability": lambda value: value == "APPLICABLE",
            "mpp_status": lambda value: value == "PASS",
            "frp_realization": lambda value: value == "FULL",
            "rank_shift": lambda value: value not in (None, "NONE"),
            "semantic_junction": lambda value: value not in (None, "NONE"),
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
        if record.get("modality_type") in (None, "NONE", "UNCLEAR"):
            error("modality metaphor requires a resolved modality type")
        if record.get("explicitness") != "EXPLICIT":
            error("modality metaphor requires EXPLICIT expanded realization")
        if not record.get("congruent_modal_rewrite"):
            error("modality metaphor requires congruent_modal_rewrite")

    if interpersonal_status == "TYPICAL_GM" and interpersonal_type == "NONE":
        error("interpersonal TYPICAL_GM requires an interpersonal type")
    if interpersonal_status == "TYPICAL_GM" and record.get("confidence") == "LOW":
        error("LOW confidence cannot support an unqualified interpersonal TYPICAL_GM")

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


def load_candidate_rule_ids(path: Path = DEFAULT_RULES) -> set[str]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys
        )
    except (OSError, json.JSONDecodeError, AnnotationInputError) as exc:
        raise ValueError(f"cannot load candidate rules {path}: {exc}") from exc
    rules = payload.get("rules") if isinstance(payload, dict) else None
    if not isinstance(rules, list):
        raise ValueError(f"candidate rules {path} must contain a rules array")
    ids = {
        str(rule.get("id"))
        for rule in rules
        if isinstance(rule, dict) and isinstance(rule.get("id"), str)
    }
    if len(ids) != len(rules):
        raise ValueError(f"candidate rules {path} contain missing or duplicate IDs")
    return ids


def validate_cross_fields_v3(
    record: dict[str, Any], label: str, candidate_rule_ids: set[str] | None = None
) -> list[str]:
    errors = validate_context_gate(record, label)

    def error(message: str) -> None:
        _append_error(errors, label, message)

    sentence = record.get("sentence")
    start = record.get("span_start")
    end = record.get("span_end")
    span = record.get("candidate_span")
    for field in (
        "document_id",
        "sentence_id",
        "sentence",
        "candidate_span",
        "actual_realization",
        "candidate_rule",
        "analyzer_version",
        "source_provenance",
    ):
        value = record.get(field)
        if not has_substantive_text(value):
            error(f"{field} must contain non-whitespace text")
    if (
        isinstance(sentence, str)
        and isinstance(start, int)
        and not isinstance(start, bool)
        and isinstance(end, int)
        and not isinstance(end, bool)
    ):
        if start >= end:
            error("span_start must be smaller than span_end")
        elif end > len(sentence):
            error("span_end exceeds the sentence length")
        elif isinstance(span, str) and sentence[start:end] != span:
            error("candidate_span must equal sentence[span_start:span_end]")

    formula = all(
        (
            record.get("mapping_mismatch") is True,
            record.get("congruent_agnate_plausible") is True,
            record.get("remapping_explicit") is True,
            record.get("lexical_only") is False,
        )
    )
    if record.get("gm_candidate") is not formula:
        error(
            "gm_candidate must equal mapping_mismatch AND "
            "congruent_agnate_plausible AND remapping_explicit AND NOT lexical_only"
        )

    if record.get("context_sufficiency") == "INSUFFICIENT" and formula:
        error("insufficient context cannot establish every GM-candidate predicate")
    if record.get("gm_candidate") is True and record.get("remapping_type") == "NONE":
        error("a GM candidate requires an explicit remapping_type")
    if record.get("lexical_only") is True:
        if record.get("gm_candidate") is not False:
            error("lexical-only evidence cannot be a GM candidate")
        if record.get("ideational_gm_status") not in ("NON_GM", "INDETERMINATE"):
            error("lexical-only evidence cannot receive an ideational GM label")
        if record.get("interpersonal_gm_status") not in ("NON_GM", "INDETERMINATE"):
            error("lexical-only evidence cannot receive an interpersonal GM label")

    statuses = (
        record.get("ideational_gm_status"),
        record.get("interpersonal_gm_status"),
    )
    if "TYPICAL_GM" in statuses:
        if record.get("gm_candidate") is not True:
            error("TYPICAL_GM requires gm_candidate=true")
        if record.get("confidence") == "LOW":
            error("LOW confidence cannot support TYPICAL_GM")
        if record.get("exclusion_reason") != "NONE":
            error("TYPICAL_GM cannot carry an exclusion reason")
        if not has_substantive_text(record.get("congruent_agnate")):
            error("TYPICAL_GM requires a non-empty congruent_agnate")
    if record.get("congruent_agnate_plausible") is not True and "TYPICAL_GM" in statuses:
        error("without a plausible congruent agnate the maximum label is MARGINAL_GM")

    if not isinstance(record.get("positive_evidence"), list) or not record.get(
        "positive_evidence"
    ):
        error("positive_evidence must contain at least one observation")
    elif any(not has_substantive_text(item) for item in record["positive_evidence"]):
        error("positive_evidence cannot contain blank observations")
    if not isinstance(record.get("counter_evidence"), list) or not record.get(
        "counter_evidence"
    ):
        error("counter_evidence must contain the strongest contrary analysis")
    elif any(not has_substantive_text(item) for item in record["counter_evidence"]):
        error("counter_evidence cannot contain blank observations")
    if not isinstance(record.get("operational_tests"), list) or not record.get(
        "operational_tests"
    ):
        error("operational_tests must record at least one applied test")
    elif any(not has_substantive_text(item) for item in record["operational_tests"]):
        error("operational_tests cannot contain blank test names")

    if (
        record.get("confidence") != "HIGH"
        or any(status in REVIEW_STATUSES for status in statuses)
    ) and record.get("needs_human_review") is not True:
        error("uncertain, marginal, or indeterminate records require human review")

    if record.get("context_sufficiency") == "PARTIAL":
        if record.get("confidence") == "HIGH":
            error("partial context cannot support HIGH confidence")
        if record.get("needs_human_review") is not True:
            error("partial context requires human review")

    if record.get("context_sufficiency") == "INSUFFICIENT":
        if not isinstance(record.get("candidate_interpretations"), list) or not record.get(
            "candidate_interpretations"
        ):
            error(
                "insufficient-context records must preserve any analysis only as "
                "candidate_interpretations"
            )
        elif any(
            not has_substantive_text(item)
            for item in record["candidate_interpretations"]
        ):
            error("candidate_interpretations cannot contain blank readings")
        conservative_fields = {
            "semantic_category": "UNCLEAR",
            "congruent_realization": None,
            "congruent_agnate": None,
            "remapping_type": "NONE",
            "mapping_mismatch": False,
            "congruent_agnate_plausible": False,
            "remapping_explicit": False,
            "lexical_only": False,
            "rank_relation": "UNCLEAR",
            "realization_degree": "UNCLEAR",
            "semantic_junction": "UNCLEAR",
            "exclusion_reason": "NO_CONTEXT",
        }
        for field, expected in conservative_fields.items():
            if record.get(field) != expected:
                error(
                    f"insufficient context keeps conditional analysis out of formal "
                    f"fields: {field} must be {expected!r}"
                )
    elif record.get("confidence") == "HIGH" and record.get("needs_human_review") is True:
        # Review is allowed for Chinese MPP and adjudication; this is not an error.
        pass

    candidate_rule = record.get("candidate_rule")
    if candidate_rule_ids is not None and (
        not isinstance(candidate_rule, str) or candidate_rule not in candidate_rule_ids
    ):
        error(f"unknown candidate_rule {candidate_rule!r}")

    if record.get("source_provenance") and PRIVATE_ABSOLUTE_PATH.search(
        str(record["source_provenance"])
    ):
        error("source_provenance must not expose a private absolute path")

    remapping = record.get("remapping_type")
    if (
        record.get("ideational_gm_status") == "TYPICAL_GM"
        and remapping in NOMINALIZING_V3_REMAPPINGS
        and record.get("framework_profile") == "HALLIDAY_PLUS_YANG_OPERATIONAL"
    ):
        gates = {
            "rank_relation": record.get("rank_relation") not in ("NONE", "UNCLEAR"),
            "realization_degree": record.get("realization_degree") == "FULL",
            "semantic_junction": record.get("semantic_junction") not in ("NONE", "UNCLEAR"),
        }
        for field, passed in gates.items():
            if not passed:
                error(f"typical nominalizing GM failed gate: {field}")
        mpp = record.get("mpp")
        if not isinstance(mpp, dict) or mpp.get("status") != "PASS":
            error("typical nominalizing GM requires mpp.status=PASS")

    mpp = record.get("mpp")
    if isinstance(mpp, dict):
        applicability = mpp.get("applicability")
        status = mpp.get("status")
        if applicability == "APPLICABLE":
            if not mpp.get("candidate_agnates"):
                error("applicable MPP requires candidate_agnates")
            if status not in ("PASS", "FAIL", "UNCLEAR"):
                error("applicable MPP requires PASS, FAIL, or UNCLEAR")
        if applicability == "NOT_APPLICABLE":
            if status != "NOT_APPLICABLE" or mpp.get("agnation_level") != "NOT_APPLICABLE":
                error("non-applicable MPP requires NOT_APPLICABLE status and level")
            if mpp.get("candidate_agnates") or mpp.get("selected_agnate") is not None:
                error("non-applicable MPP cannot contain selected or candidate agnates")
        if applicability == "UNCLEAR" and status != "UNCLEAR":
            error("unclear MPP applicability requires status=UNCLEAR")
        if status in ("PASS", "FAIL") and applicability != "APPLICABLE":
            error(f"MPP {status} requires applicability=APPLICABLE")
        if status == "PASS":
            if not mpp.get("selected_agnate"):
                error("MPP PASS requires selected_agnate")
            elif not isinstance(mpp.get("candidate_agnates"), list) or not any(
                mpp.get("selected_agnate") == candidate
                for candidate in mpp.get("candidate_agnates", [])
            ):
                error("MPP selected_agnate must occur in candidate_agnates")
            if mpp.get("higher_priority_available") is True:
                error("MPP cannot PASS while a higher-priority agnate is available")
        if status == "FAIL" and not mpp.get("violation_reason"):
            error("MPP FAIL requires violation_reason")
        if (
            status == "FAIL"
            and record.get("ideational_gm_status") == "TYPICAL_GM"
            and remapping in NOMINALIZING_V3_REMAPPINGS
        ):
            error("MPP FAIL cannot receive TYPICAL_GM")
        if record.get("language") == "zh" and applicability != "NOT_APPLICABLE":
            if mpp.get("crosslinguistic_caution") is not True:
                error("Chinese MPP requires crosslinguistic_caution=true")
            if record.get("needs_human_review") is not True:
                error("Chinese MPP requires human review")
            if applicability == "APPLICABLE" and not str(
                mpp.get("agnation_level", "")
            ).startswith("ZH_"):
                error("Chinese MPP requires a ZH_* agnation level")
        if (
            record.get("language") == "en"
            and applicability == "APPLICABLE"
            and str(mpp.get("agnation_level", "")).startswith("ZH_")
        ):
            error("English MPP cannot use a ZH_* agnation level")

    if record.get("polarity_metaphor") is True:
        if record.get("polarity_subtype", "NONE") == "NONE":
            error("polarity_metaphor=true requires a polarity_subtype")
    elif record.get("polarity_subtype", "NONE") != "NONE":
        error("polarity_subtype must be NONE when polarity_metaphor=false")
    return errors


def record_schema_version(record: Any, forced: str = "auto") -> str:
    if forced in ("2", "3"):
        return forced
    if isinstance(record, dict):
        declared = record.get("schema_version")
        if declared == "3.0":
            return "3"
        if declared is None or declared == "2.0":
            return "2"
        raise ValueError(f"unsupported schema_version {declared!r}")
    return "3"


def load_schema(path: Path) -> dict[str, Any]:
    try:
        schema = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys
        )
    except (OSError, json.JSONDecodeError, AnnotationInputError) as exc:
        raise ValueError(f"cannot load schema {path}: {exc}") from exc
    if not isinstance(schema, dict):
        raise ValueError(f"schema {path} must be a JSON object")
    return schema


def validate_record(
    record: Any,
    label: str = "record",
    schema_version: str = "auto",
    schemas: dict[str, dict[str, Any]] | None = None,
    candidate_rule_ids: set[str] | None = None,
) -> list[str]:
    schemas = schemas or {version: load_schema(path) for version, path in SCHEMA_PATHS.items()}
    version = record_schema_version(record, schema_version)
    errors = validate_shape(record, schemas[version], label)
    # Cross-field invariants are deliberately checked even when a shape error was
    # found. This makes safety-gate failures explicit instead of hiding them behind
    # the first JSON-Schema diagnostic.
    if isinstance(record, dict):
        if version == "3":
            errors.extend(validate_cross_fields_v3(record, label, candidate_rule_ids))
        else:
            errors.extend(validate_cross_fields_v2(record, label))
    return errors


def _container_to_records(payload: Any, path: Path) -> list[dict[str, Any]]:
    records = payload if isinstance(payload, list) else [payload]
    if not records:
        raise AnnotationInputError(f"{path} contains no annotation records")
    if not all(isinstance(record, dict) for record in records):
        raise AnnotationInputError(f"{path} must contain only JSON objects")
    return records


def _detect_format(path: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    suffix = path.suffix.lower()
    if suffix in (".jsonl", ".ndjson"):
        return "jsonl"
    if suffix == ".csv":
        return "csv"
    return "json"


def _csv_spec_for_key(key: str, schemas: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    for version in ("3", "2"):
        spec = schemas[version].get("properties", {}).get(key)
        if isinstance(spec, dict):
            return resolve_ref(schemas[version], spec)
    return None


def _parse_csv_cell(
    key: str, raw: str, schemas: dict[str, dict[str, Any]], row_number: int
) -> Any:
    spec = _csv_spec_for_key(key, schemas)
    if spec is None:
        return raw
    expected = spec.get("type")
    accepted = [expected] if isinstance(expected, str) else list(expected or [])
    if raw == "null" and "null" in accepted:
        return None
    try:
        if "array" in accepted or "object" in accepted:
            return json.loads(raw, object_pairs_hook=reject_duplicate_keys)
        if "boolean" in accepted:
            if raw not in ("true", "false"):
                raise ValueError("expected true or false")
            return raw == "true"
        if "integer" in accepted:
            return int(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        raise AnnotationInputError(
            f"CSV row {row_number} field {key!r} cannot be decoded: {exc}"
        ) from exc
    if "string" in accepted and raw.lstrip().startswith(("=", "+", "-", "@")):
        raise AnnotationInputError(
            f"CSV row {row_number} field {key!r} begins with a spreadsheet-formula prefix; "
            "use JSONL or prefix the literal value with an apostrophe"
        )
    return raw


def _load_csv(path: Path, schemas: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    csv.field_size_limit(CSV_FIELD_LIMIT)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = csv.reader(handle)
        try:
            header = next(rows)
        except StopIteration as exc:
            raise AnnotationInputError(f"{path} contains no annotation records") from exc
        if not header or any(not cell for cell in header):
            raise AnnotationInputError(f"{path} has an empty CSV header")
        duplicates = sorted({cell for cell in header if header.count(cell) > 1})
        if duplicates:
            raise AnnotationInputError(
                f"{path} has duplicate CSV headers: {', '.join(duplicates)}"
            )
        records: list[dict[str, Any]] = []
        for row_number, row in enumerate(rows, start=2):
            if not row or all(not cell for cell in row):
                continue
            if len(row) != len(header):
                raise AnnotationInputError(
                    f"{path} CSV row {row_number} has {len(row)} cells; expected {len(header)}"
                )
            if any("\x00" in cell for cell in row):
                raise AnnotationInputError(f"{path} CSV row {row_number} contains NUL")
            records.append(
                {
                    key: _parse_csv_cell(key, raw, schemas, row_number)
                    for key, raw in zip(header, row)
                }
            )
    if not records:
        raise AnnotationInputError(f"{path} contains no annotation records")
    return records


def load_records(
    path: Path,
    input_format: str = "auto",
    schemas: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    schemas = schemas or {version: load_schema(schema) for version, schema in SCHEMA_PATHS.items()}
    detected = _detect_format(path, input_format)
    if detected == "csv":
        return _load_csv(path, schemas)
    if detected == "jsonl":
        records: list[dict[str, Any]] = []
        with path.open(encoding="utf-8-sig") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line, object_pairs_hook=reject_duplicate_keys)
                except (json.JSONDecodeError, AnnotationInputError) as exc:
                    message = exc.msg if isinstance(exc, json.JSONDecodeError) else str(exc)
                    raise AnnotationInputError(
                        f"{path}:{line_number}: invalid JSONL: {message}"
                    ) from exc
                if not isinstance(payload, dict):
                    raise AnnotationInputError(
                        f"{path}:{line_number}: every JSONL line must be an object"
                    )
                records.append(payload)
        if not records:
            raise AnnotationInputError(f"{path} contains no annotation records")
        return records
    try:
        with path.open(encoding="utf-8-sig") as handle:
            return _container_to_records(
                json.load(handle, object_pairs_hook=reject_duplicate_keys), path
            )
    except (json.JSONDecodeError, AnnotationInputError) as exc:
        message = exc.msg if isinstance(exc, json.JSONDecodeError) else str(exc)
        raise AnnotationInputError(f"{path}: invalid JSON: {message}") from exc


def validate_batch_uniqueness(
    records: Iterable[dict[str, Any]], path: Path, schema_version: str
) -> list[str]:
    if schema_version == "2":
        return []
    seen: set[str] = set()
    errors: list[str] = []
    for index, record in enumerate(records):
        if record.get("schema_version") != "3.0":
            continue
        identity = (
            record.get("document_id"),
            record.get("sentence_id"),
            record.get("span_start"),
            record.get("span_end"),
        )
        identity_key = json.dumps(identity, ensure_ascii=False, sort_keys=True)
        if identity_key in seen:
            errors.append(f"{path}[{index}]: duplicate annotation identity {identity!r}")
        seen.add(identity_key)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Halliday SFL GM annotation v2/v3 JSON, JSONL, or CSV records."
    )
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument(
        "--format",
        choices=("auto", "json", "jsonl", "csv"),
        default="auto",
        help="Input container; auto uses the file extension.",
    )
    parser.add_argument(
        "--schema-version",
        choices=("auto", "2", "3"),
        default="auto",
        help="Auto treats schema_version=3.0 as v3 and unversioned records as v2.",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        help="Use one custom schema for all records (advanced/testing only).",
    )
    parser.add_argument(
        "--candidate-rules",
        type=Path,
        default=DEFAULT_RULES,
        help="External JSON-compatible YAML rule inventory used by Schema v3.",
    )
    args = parser.parse_args(argv)

    try:
        schemas = {version: load_schema(path) for version, path in SCHEMA_PATHS.items()}
        if args.schema:
            custom = load_schema(args.schema)
            if args.schema_version == "auto":
                parser.error("--schema requires --schema-version 2 or 3")
            schemas[args.schema_version] = custom
        candidate_rule_ids = load_candidate_rule_ids(args.candidate_rules)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    failures = 0
    input_failures = 0
    checked = 0
    for path in args.files:
        try:
            records = load_records(path, args.format, schemas)
        except (OSError, AnnotationInputError, ValueError) as exc:
            print(f"ERROR {path}: {exc}", file=sys.stderr)
            failures += 1
            input_failures += 1
            continue

        file_errors: list[str] = []
        for index, record in enumerate(records):
            checked += 1
            label = f"{path}[{index}]" if len(records) > 1 else str(path)
            try:
                file_errors.extend(
                    validate_record(
                        record,
                        label,
                        args.schema_version,
                        schemas,
                        candidate_rule_ids,
                    )
                )
            except (ValueError, TypeError) as exc:
                file_errors.append(f"{label}: {exc}")
        file_errors.extend(validate_batch_uniqueness(records, path, args.schema_version))

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
        return 2 if input_failures else 1
    print(f"Validation passed: {checked} record(s) checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
