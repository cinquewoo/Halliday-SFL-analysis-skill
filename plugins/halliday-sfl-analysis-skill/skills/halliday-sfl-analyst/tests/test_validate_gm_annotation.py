#!/usr/bin/env python3
"""Independent unit and CLI tests for validate_gm_annotation.py."""

from __future__ import annotations

import contextlib
import copy
import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
SCRIPT_DIR = TEST_DIR.parent / "scripts"
sys.path.insert(0, str(TEST_DIR))
sys.path.insert(0, str(SCRIPT_DIR))

import validate_gm_annotation as validator  # noqa: E402
from gold_fixture import load_gold  # noqa: E402


def legacy_v2_record() -> dict[str, object]:
    return {
        "schema_version": "2.0",
        "item_id": "legacy-1",
        "text": "They decided.",
        "context": "A complete constructed clause.",
        "language": "en",
        "unit_type": "CLAUSE",
        "context_sufficiency": "SUFFICIENT",
        "ideational_gm_status": "NON_GM",
        "ideational_type": "NONE",
        "congruent_agnate": "They decided.",
        "source_semantic_category": "PROCESS",
        "source_rank": "CLAUSE",
        "target_grammatical_category": "VERBAL",
        "target_rank": "CLAUSE",
        "rank_shift": "NONE",
        "semantic_junction": "NONE",
        "frp_realization": "NONE",
        "mpp_applicability": "NOT_APPLICABLE",
        "mpp_candidate_agnates": [],
        "mpp_selected_agnate": None,
        "mpp_agnation_level": "NOT_APPLICABLE",
        "mpp_status": "NOT_APPLICABLE",
        "mpp_higher_priority_available": False,
        "mpp_violation_reason": None,
        "mpp_crosslinguistic_caution": False,
        "interpersonal_gm_status": "NON_GM",
        "interpersonal_type": "NONE",
        "speech_function": "GIVE_INFORMATION",
        "mood_form": "DECLARATIVE",
        "mood_mismatch": False,
        "as_if_relation": None,
        "modality_type": "NONE",
        "orientation": "NONE",
        "explicitness": "NONE",
        "congruent_modal_rewrite": None,
        "polarity_metaphor": False,
        "polarity_subtype": "NONE",
        "exclusion_reason": "NONE",
        "evidence": ["finite Process realizes an event"],
        "counterevidence": ["a nominal agnate exists but is not selected"],
        "confidence": "HIGH",
        "needs_human_review": False,
    }


class ValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _, cls.gold = load_gold()
        cls.schemas = {
            version: validator.load_schema(path)
            for version, path in validator.SCHEMA_PATHS.items()
        }
        cls.rules = validator.load_candidate_rule_ids()
        cls.valid_v3 = copy.deepcopy(
            next(record for record in cls.gold if record["sentence_id"] == "en-002")
        )
        cls.insufficient_v3 = copy.deepcopy(
            next(record for record in cls.gold if record["sentence_id"] == "boundary-001")
        )

    def errors(self, record: dict[str, object]) -> list[str]:
        return validator.validate_record(
            record,
            schemas=self.schemas,
            candidate_rule_ids=self.rules,
        )

    def test_valid_v3_and_legacy_v2(self) -> None:
        self.assertEqual(self.errors(self.valid_v3), [])
        self.assertEqual(self.errors(legacy_v2_record()), [])

    def test_insufficient_context_positive_case(self) -> None:
        self.assertEqual(self.errors(self.insufficient_v3), [])

    def test_regression_insufficient_word_cannot_be_typical_or_high(self) -> None:
        broken = copy.deepcopy(self.insufficient_v3)
        broken.update(
            ideational_gm_status="TYPICAL_GM",
            interpersonal_gm_status="NON_GM",
            confidence="HIGH",
            needs_human_review=False,
        )
        errors = "\n".join(self.errors(broken))
        self.assertIn("ideational_gm_status='INDETERMINATE'", errors)
        self.assertIn("interpersonal_gm_status='INDETERMINATE'", errors)
        self.assertIn("confidence='LOW'", errors)
        self.assertIn("needs_human_review=True", errors)

    def test_regression_legacy_v2_context_gate(self) -> None:
        broken = legacy_v2_record()
        broken.update(
            context_sufficiency="INSUFFICIENT",
            ideational_gm_status="TYPICAL_GM",
            interpersonal_gm_status="INDETERMINATE",
            confidence="HIGH",
            needs_human_review=True,
        )
        errors = "\n".join(self.errors(broken))
        self.assertIn("ideational_gm_status='INDETERMINATE'", errors)
        self.assertIn("confidence='LOW'", errors)

    def test_legacy_word_repeated_as_context_is_still_isolated(self) -> None:
        broken = legacy_v2_record()
        broken.update(
            text="development",
            context="“development”.",
            unit_type="WORD",
            context_sufficiency="SUFFICIENT",
        )
        self.assertIn(
            "isolated WORD without co-text",
            "\n".join(self.errors(broken)),
        )

    def test_insufficient_context_requires_candidate_interpretations(self) -> None:
        broken = copy.deepcopy(self.insufficient_v3)
        broken["candidate_interpretations"] = []
        self.assertIn(
            "candidate_interpretations",
            "\n".join(self.errors(broken)),
        )

    def test_isolated_word_cannot_self_declare_sufficient_context(self) -> None:
        broken = copy.deepcopy(self.valid_v3)
        broken.update(
            sentence="rejection",
            candidate_span="rejection",
            span_start=0,
            span_end=9,
            unit_type="WORD",
            context_before="",
            context_after="",
            context_sufficiency="SUFFICIENT",
        )
        self.assertIn(
            "isolated WORD without co-text",
            "\n".join(self.errors(broken)),
        )

    def test_punctuation_and_wrappers_do_not_fake_word_context(self) -> None:
        for sentence, before in (
            ("rejection.", ""),
            ('“rejection”', ""),
            ("rejection", "."),
        ):
            broken = copy.deepcopy(self.valid_v3)
            broken.update(
                sentence=sentence,
                candidate_span="rejection",
                span_start=sentence.index("rejection"),
                span_end=sentence.index("rejection") + len("rejection"),
                unit_type="WORD",
                context_before=before,
                context_after="",
                context_sufficiency="SUFFICIENT",
            )
            self.assertIn(
                "isolated WORD without co-text",
                "\n".join(self.errors(broken)),
            )

    def test_insufficient_context_keeps_mapping_only_in_candidate_readings(self) -> None:
        broken = copy.deepcopy(self.insufficient_v3)
        broken.update(
            semantic_category="PROCESS",
            congruent_realization="某事物发展",
            congruent_agnate="某事物发展",
            remapping_type="PROCESS_TO_THING",
            mapping_mismatch=True,
            congruent_agnate_plausible=True,
        )
        errors = "\n".join(self.errors(broken))
        self.assertIn("conditional analysis out of formal fields", errors)
        self.assertIn("congruent_agnate", errors)

    def test_candidate_formula_is_exact(self) -> None:
        broken = copy.deepcopy(self.valid_v3)
        broken["mapping_mismatch"] = False
        errors = "\n".join(self.errors(broken))
        self.assertIn("gm_candidate must equal", errors)

    def test_typical_label_requires_candidate_true(self) -> None:
        broken = copy.deepcopy(self.valid_v3)
        broken["gm_candidate"] = False
        self.assertIn(
            "TYPICAL_GM requires gm_candidate=true",
            "\n".join(self.errors(broken)),
        )

    def test_no_agnate_caps_positive_label(self) -> None:
        broken = copy.deepcopy(self.valid_v3)
        broken.update(congruent_agnate=None, congruent_agnate_plausible=False, gm_candidate=False)
        errors = "\n".join(self.errors(broken))
        self.assertIn("maximum label is MARGINAL_GM", errors)

    def test_typical_label_requires_materialized_agnate(self) -> None:
        for value in (None, "", " ", "\u200b", "\x00", ".", "——", "🙂", "\u0301"):
            broken = copy.deepcopy(self.valid_v3)
            broken["congruent_agnate"] = value
            broken["congruent_realization"] = value
            self.assertIn(
                "TYPICAL_GM requires a non-empty congruent_agnate",
                "\n".join(self.errors(broken)),
            )

    def test_partial_context_is_reviewed_and_not_high_confidence(self) -> None:
        broken = copy.deepcopy(self.valid_v3)
        broken.update(context_sufficiency="PARTIAL", confidence="HIGH", needs_human_review=False)
        errors = "\n".join(self.errors(broken))
        self.assertIn("partial context cannot support HIGH confidence", errors)
        self.assertIn("partial context requires human review", errors)

    def test_mpp_fail_cannot_be_typical_even_in_core_profile(self) -> None:
        broken = copy.deepcopy(self.valid_v3)
        broken["mpp"] = {
            "applicability": "APPLICABLE",
            "candidate_agnates": ["The committee rejected the proposal."],
            "selected_agnate": "The committee rejected the proposal.",
            "agnation_level": "DERIVATIONAL_AGNATION",
            "status": "FAIL",
            "higher_priority_available": True,
            "violation_reason": "constructed regression failure",
            "crosslinguistic_caution": False,
        }
        self.assertIn("MPP FAIL cannot receive TYPICAL_GM", "\n".join(self.errors(broken)))

    def test_mpp_pass_requires_applicable_inventory_and_language_level(self) -> None:
        broken = copy.deepcopy(self.valid_v3)
        broken["mpp"] = {
            "applicability": "UNCLEAR",
            "candidate_agnates": [],
            "selected_agnate": "remote form",
            "agnation_level": "ZH_SAME_CORE_MORPHEME",
            "status": "PASS",
            "higher_priority_available": False,
            "violation_reason": None,
            "crosslinguistic_caution": False,
        }
        errors = "\n".join(self.errors(broken))
        self.assertIn("unclear MPP applicability requires status=UNCLEAR", errors)
        self.assertIn("MPP PASS requires applicability=APPLICABLE", errors)
        self.assertIn("selected_agnate must occur in candidate_agnates", errors)

    def test_span_type_bounds_and_text_are_checked(self) -> None:
        for field, value, expected in (
            ("span_start", True, "expected integer"),
            ("span_end", 999, "exceeds the sentence length"),
            ("candidate_span", "wrong", "must equal sentence"),
        ):
            broken = copy.deepcopy(self.valid_v3)
            broken[field] = value
            self.assertIn(expected, "\n".join(self.errors(broken)))

    def test_schema_required_enum_and_additional_properties(self) -> None:
        missing = copy.deepcopy(self.valid_v3)
        del missing["document_id"]
        self.assertIn("missing fields: document_id", "\n".join(self.errors(missing)))
        enum = copy.deepcopy(self.valid_v3)
        enum["confidence"] = "CERTAIN"
        self.assertIn("invalid enum", "\n".join(self.errors(enum)))
        extra = copy.deepcopy(self.valid_v3)
        extra["secret"] = "no"
        self.assertIn("unexpected fields: secret", "\n".join(self.errors(extra)))

    def test_evidence_and_tests_reject_whitespace_only_items(self) -> None:
        broken = copy.deepcopy(self.valid_v3)
        broken["positive_evidence"] = [" "]
        broken["counter_evidence"] = ["\t"]
        broken["operational_tests"] = ["\n"]
        errors = "\n".join(self.errors(broken))
        self.assertIn("positive_evidence cannot contain blank", errors)
        self.assertIn("counter_evidence cannot contain blank", errors)
        self.assertIn("operational_tests cannot contain blank", errors)

    def test_evidence_requires_lexical_content_not_punctuation_or_symbols(self) -> None:
        for value in (".", "——", "🙂", "\u0301"):
            broken = copy.deepcopy(self.valid_v3)
            broken["positive_evidence"] = [value]
            broken["counter_evidence"] = [value]
            broken["operational_tests"] = [value]
            errors = "\n".join(self.errors(broken))
            self.assertIn("positive_evidence cannot contain blank", errors)
            self.assertIn("counter_evidence cannot contain blank", errors)
            self.assertIn("operational_tests cannot contain blank", errors)

    def test_private_absolute_path_is_not_valid_provenance(self) -> None:
        broken = copy.deepcopy(self.valid_v3)
        broken["source_provenance"] = "file:///Users/example/private/source.pdf"
        self.assertIn(
            "must not expose a private absolute path",
            "\n".join(self.errors(broken)),
        )

    def test_single_array_jsonl_and_csv_load(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            single = root / "one.json"
            array = root / "many.json"
            jsonl = root / "many.jsonl"
            csv_path = root / "one.csv"
            single.write_text(json.dumps(self.valid_v3, ensure_ascii=False), encoding="utf-8")
            array.write_text(json.dumps([self.valid_v3], ensure_ascii=False), encoding="utf-8")
            jsonl.write_text(json.dumps(self.valid_v3, ensure_ascii=False) + "\n", encoding="utf-8")
            with csv_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(self.valid_v3.keys())
                writer.writerow(
                    json.dumps(value, ensure_ascii=False)
                    if isinstance(value, (list, dict))
                    else "null"
                    if value is None
                    else str(value).lower()
                    if isinstance(value, bool)
                    else value
                    for value in self.valid_v3.values()
                )
            for path in (single, array, jsonl, csv_path):
                records = validator.load_records(path, schemas=self.schemas)
                self.assertEqual(len(records), 1)
                self.assertEqual(self.errors(records[0]), [])

    def test_empty_and_malformed_containers_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {
                "empty.json": "[]",
                "empty.jsonl": "\n",
                "bad.jsonl": "{bad}\n",
                "empty.csv": "schema_version\n",
                "duplicate.csv": "schema_version,schema_version\n3.0,3.0\n",
            }
            for name, content in files.items():
                path = root / name
                path.write_text(content, encoding="utf-8")
                with self.assertRaises(validator.AnnotationInputError, msg=name):
                    validator.load_records(path, schemas=self.schemas)

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            duplicate_json = root / "duplicate.json"
            duplicate_jsonl = root / "duplicate.jsonl"
            payload = '{"context_sufficiency":"INSUFFICIENT","context_sufficiency":"SUFFICIENT"}'
            duplicate_json.write_text(payload, encoding="utf-8")
            duplicate_jsonl.write_text(payload + "\n", encoding="utf-8")
            for path in (duplicate_json, duplicate_jsonl):
                with self.assertRaisesRegex(validator.AnnotationInputError, "duplicate JSON key"):
                    validator.load_records(path, schemas=self.schemas)

    def test_csv_requires_lowercase_booleans_and_rejects_formula_prefixes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            uppercase = root / "uppercase.csv"
            formula = root / "formula.csv"
            uppercase.write_text(
                "schema_version,needs_human_review\n3.0,TRUE\n", encoding="utf-8"
            )
            formula.write_text(
                "schema_version,notes\n3.0,=HYPERLINK(\"https://example.invalid\")\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(validator.AnnotationInputError, "expected true or false"):
                validator.load_records(uppercase, schemas=self.schemas)
            with self.assertRaisesRegex(validator.AnnotationInputError, "formula prefix"):
                validator.load_records(formula, schemas=self.schemas)

    def test_cli_returns_zero_one_and_two(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            valid = root / "valid.json"
            invalid = root / "invalid.json"
            malformed = root / "malformed.json"
            valid.write_text(json.dumps(self.valid_v3, ensure_ascii=False), encoding="utf-8")
            broken = copy.deepcopy(self.insufficient_v3)
            broken["confidence"] = "HIGH"
            invalid.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
            malformed.write_text("{", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(validator.main([str(valid)]), 0)
                self.assertEqual(validator.main([str(invalid)]), 1)
                self.assertEqual(validator.main([str(malformed)]), 2)

    def test_malformed_field_types_report_errors_without_crashing(self) -> None:
        mutations = (
            ("schema-version-list", {"schema_version": ["3.0"]}),
            ("identity-list", {"document_id": ["not", "scalar"]}),
            ("mpp-status-list", {"mpp": {"status": ["PASS"]}}),
            ("candidate-rule-list", {"candidate_rule": ["NOM_PROCESS"]}),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, updates in mutations:
                broken = copy.deepcopy(self.valid_v3)
                broken.update(updates)
                path = root / f"{name}.json"
                path.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
                with self.subTest(name=name), contextlib.redirect_stdout(
                    io.StringIO()
                ), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(validator.main([str(path)]), 1)

    def test_library_api_rejects_non_array_evidence_without_type_error(self) -> None:
        for field in (
            "positive_evidence",
            "counter_evidence",
            "operational_tests",
        ):
            for value in (True, 7, 2.5, {"not": "an array"}):
                broken = copy.deepcopy(self.valid_v3)
                broken[field] = value
                with self.subTest(field=field, value=value):
                    self.assertTrue(self.errors(broken))
        for value in (True, 7, 2.5, {"not": "an array"}):
            broken = copy.deepcopy(self.insufficient_v3)
            broken["candidate_interpretations"] = value
            with self.subTest(field="candidate_interpretations", value=value):
                self.assertTrue(self.errors(broken))

    def test_batch_uniqueness_tolerates_invalid_identity_types(self) -> None:
        broken = copy.deepcopy(self.valid_v3)
        broken["document_id"] = ["invalid", "but JSON-serializable"]
        errors = validator.validate_batch_uniqueness([broken, broken], Path("batch.json"), "auto")
        self.assertEqual(len(errors), 1)


if __name__ == "__main__":
    unittest.main()
