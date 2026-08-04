#!/usr/bin/env python3
"""Gold-data coverage and Schema v3 regression tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
SCRIPT_DIR = TEST_DIR.parent / "scripts"
sys.path.insert(0, str(TEST_DIR))
sys.path.insert(0, str(SCRIPT_DIR))

import validate_gm_annotation  # noqa: E402
from gold_fixture import load_gold  # noqa: E402


class GoldFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload, cls.records = load_gold()
        cls.by_sentence = {record["sentence"]: record for record in cls.records}
        cls.schemas = {
            version: validate_gm_annotation.load_schema(path)
            for version, path in validate_gm_annotation.SCHEMA_PATHS.items()
        }
        cls.rule_ids = validate_gm_annotation.load_candidate_rule_ids()

    def test_has_at_least_thirty_unique_cases(self) -> None:
        self.assertEqual(len(self.records), 43)
        self.assertGreaterEqual(len(self.records), 30)
        identities = {record["sentence_id"] for record in self.records}
        self.assertEqual(len(identities), len(self.records))

    def test_every_expanded_record_is_valid_v3(self) -> None:
        failures: list[str] = []
        for record in self.records:
            failures.extend(
                validate_gm_annotation.validate_record(
                    record,
                    label=record["sentence_id"],
                    schemas=self.schemas,
                    candidate_rule_ids=self.rule_ids,
                )
            )
        self.assertEqual(failures, [])

    def test_candidate_spans_are_unicode_codepoint_exact(self) -> None:
        for record in self.records:
            self.assertEqual(
                record["sentence"][record["span_start"] : record["span_end"]],
                record["candidate_span"],
                record["sentence_id"],
            )

    def test_required_minimal_contrasts_are_present(self) -> None:
        required = {
            "年轻人选择躺平。",
            "年轻人的躺平引发了讨论。",
            "看到结局，我瞬间破防了。",
            "网友的集体破防成为传播热点。",
            "人口迅速增长，资源压力随之上升。",
            "人口的迅速增长带来了资源压力。",
            "学生走进教室。",
            "他的到来改变了局面。",
            "桌子很大。",
        }
        self.assertTrue(required.issubset(self.by_sentence))

    def test_process_clause_and_nominal_group_contrasts(self) -> None:
        pairs = [
            ("年轻人选择躺平。", "年轻人的躺平引发了讨论。"),
            ("看到结局，我瞬间破防了。", "网友的集体破防成为传播热点。"),
            ("人口迅速增长，资源压力随之上升。", "人口的迅速增长带来了资源压力。"),
            ("学生走进教室。", "他的到来改变了局面。"),
            ("They decided.", "A decision was made."),
        ]
        for congruent, metaphorical in pairs:
            self.assertEqual(self.by_sentence[congruent]["ideational_gm_status"], "NON_GM")
            self.assertEqual(
                self.by_sentence[metaphorical]["ideational_gm_status"], "TYPICAL_GM"
            )
            self.assertNotEqual(self.by_sentence[metaphorical]["remapping_type"], "NONE")
            self.assertTrue(self.by_sentence[metaphorical]["congruent_agnate"])

    def test_lexical_metaphor_and_rank_shift_are_not_gm(self) -> None:
        lexical = self.by_sentence["The city is a sleeping giant."]
        self.assertTrue(lexical["lexical_only"])
        self.assertFalse(lexical["gm_candidate"])
        self.assertEqual(lexical["ideational_gm_status"], "NON_GM")
        for sentence in (
            "The fact that the sample melted surprised us.",
            "What he proposed was accepted.",
            "The man who arrived yesterday waved.",
        ):
            record = self.by_sentence[sentence]
            self.assertEqual(record["exclusion_reason"], "ORDINARY_RANK_SHIFT")
            self.assertEqual(record["ideational_gm_status"], "NON_GM")

    def test_interpersonal_and_polarity_cases_are_independent(self) -> None:
        request = self.by_sentence["Could you close the window?"]
        offer = self.by_sentence["Would you like some tea?"]
        polarity = self.by_sentence["I don't think he is coming."]
        self.assertEqual(request["interpersonal_gm_status"], "TYPICAL_GM")
        self.assertEqual(request["ideational_gm_status"], "NON_GM")
        self.assertEqual(offer["interpersonal_gm_status"], "NON_GM")
        self.assertTrue(polarity["polarity_metaphor"])
        self.assertEqual(polarity["polarity_subtype"], "NEGATIVE_TRANSFER")

    def test_insufficient_context_is_low_confidence_and_reviewed(self) -> None:
        for sentence in ("发展", "bank"):
            record = self.by_sentence[sentence]
            self.assertEqual(record["context_sufficiency"], "INSUFFICIENT")
            self.assertEqual(record["ideational_gm_status"], "INDETERMINATE")
            self.assertEqual(record["interpersonal_gm_status"], "INDETERMINATE")
            self.assertEqual(record["confidence"], "LOW")
            self.assertTrue(record["needs_human_review"])
            self.assertFalse(record["gm_candidate"])
            self.assertTrue(record["candidate_interpretations"])

    def test_coverage_inventory_contains_requested_families(self) -> None:
        coverage = {
            tag for case in self.payload["cases"] for tag in case.get("coverage", [])
        }
        expected = {
            "process_to_thing",
            "figure_to_nominal_group",
            "quality_to_thing",
            "logical_relation_to_process",
            "logical_relation_to_thing",
            "ordinary_entity_noun",
            "ordinary_event_clause",
            "lexical_metaphor",
            "lexicalized_event_noun",
            "ordinary_embedding",
            "zh_zero_derivation",
            "interpersonal_mood_metaphor",
            "polarity_metaphor",
            "isolated_word",
            "insufficient_context",
        }
        self.assertTrue(expected.issubset(coverage), expected - coverage)


if __name__ == "__main__":
    unittest.main()
