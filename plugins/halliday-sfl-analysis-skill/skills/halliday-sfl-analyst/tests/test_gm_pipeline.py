#!/usr/bin/env python3
"""Tests for the lightweight GM pipeline extension points."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
SCRIPT_DIR = TEST_DIR.parent / "scripts"
sys.path.insert(0, str(TEST_DIR))
sys.path.insert(0, str(SCRIPT_DIR))

import gm_pipeline  # noqa: E402
from gold_fixture import load_gold  # noqa: E402


class GMPipelineTests(unittest.TestCase):
    def test_external_rules_load_and_have_unique_ids(self) -> None:
        rules = gm_pipeline.load_rules()
        ids = [rule["id"] for rule in rules]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("PROCESS_NOMINAL_GROUP", ids)
        self.assertIn("CONTEXT_INSUFFICIENT", ids)

    def test_extractor_only_nominates_a_unicode_span(self) -> None:
        candidates = gm_pipeline.RuleCandidateExtractor().extract(
            "人口的迅速增长带来了压力。", "zh"
        )
        growth = next(item for item in candidates if item.span == "增长")
        self.assertEqual(growth.sentence[growth.start : growth.end], "增长")
        self.assertFalse(hasattr(growth, "ideational_gm_status"))

    def test_unresolved_analyzer_never_promotes_surface_hit(self) -> None:
        candidate = gm_pipeline.Candidate(
            sentence="development",
            span="development",
            start=0,
            end=11,
            rule_id="PROCESS_NOMINAL_GROUP",
            family="ideational",
            remapping_hint="PROCESS_TO_THING",
            language="en",
        )
        analysis = gm_pipeline.UnresolvedSemanticAnalyzer().analyze(candidate, {})
        decision = gm_pipeline.ConservativeGMDecisionEngine().decide(candidate, analysis)
        self.assertFalse(decision.gm_candidate)
        self.assertEqual(decision.ideational_gm_status, "INDETERMINATE")
        self.assertEqual(decision.confidence, "LOW")
        self.assertTrue(decision.needs_human_review)

    def test_decision_formula_and_lexical_exclusion(self) -> None:
        candidate = gm_pipeline.Candidate(
            sentence="The rejection caused concern.",
            span="rejection",
            start=4,
            end=13,
            rule_id="PROCESS_NOMINAL_GROUP",
            family="ideational",
            remapping_hint="PROCESS_TO_THING",
            language="en",
        )
        evidence = gm_pipeline.SemanticAnalysis(
            context_sufficiency="SUFFICIENT",
            mapping_mismatch=True,
            congruent_agnate_plausible=True,
            remapping_explicit=True,
            lexical_only=False,
            congruent_agnate="Someone rejected something.",
            positive_evidence=("process-to-Thing mapping",),
            counter_evidence=("possible lexicalization",),
        )
        decision = gm_pipeline.ConservativeGMDecisionEngine().decide(candidate, evidence)
        self.assertTrue(decision.gm_candidate)
        self.assertEqual(decision.ideational_gm_status, "TYPICAL_GM")
        lexical = gm_pipeline.SemanticAnalysis(
            context_sufficiency="SUFFICIENT",
            mapping_mismatch=True,
            congruent_agnate_plausible=True,
            remapping_explicit=True,
            lexical_only=True,
        )
        lexical_decision = gm_pipeline.ConservativeGMDecisionEngine().decide(candidate, lexical)
        self.assertFalse(lexical_decision.gm_candidate)
        self.assertEqual(lexical_decision.ideational_gm_status, "NON_GM")

    def test_lexical_only_without_agnate_is_still_non_gm(self) -> None:
        candidate = gm_pipeline.Candidate(
            sentence="The city is a sleeping giant.",
            span="sleeping giant",
            start=14,
            end=28,
            rule_id="LEXICAL_METAPHOR_ONLY",
            family="negative_control",
            remapping_hint="NONE",
            language="en",
        )
        analysis = gm_pipeline.SemanticAnalysis(
            context_sufficiency="SUFFICIENT",
            mapping_mismatch=True,
            congruent_agnate_plausible=False,
            remapping_explicit=True,
            lexical_only=True,
        )
        decision = gm_pipeline.ConservativeGMDecisionEngine().decide(candidate, analysis)
        self.assertEqual(decision.ideational_gm_status, "NON_GM")
        self.assertFalse(decision.gm_candidate)

    def test_no_agnate_is_at_most_borderline(self) -> None:
        candidate = gm_pipeline.Candidate(
            sentence="The reason was unclear.",
            span="reason",
            start=4,
            end=10,
            rule_id="LEXICALIZED_EVENT_NOUN",
            family="boundary",
            remapping_hint="NONE",
            language="en",
        )
        analysis = gm_pipeline.SemanticAnalysis(
            context_sufficiency="PARTIAL",
            mapping_mismatch=True,
            congruent_agnate_plausible=False,
            remapping_explicit=True,
            lexical_only=False,
        )
        decision = gm_pipeline.ConservativeGMDecisionEngine().decide(candidate, analysis)
        self.assertFalse(decision.gm_candidate)
        self.assertEqual(decision.ideational_gm_status, "MARGINAL_GM")
        self.assertTrue(decision.needs_human_review)

    def test_partial_context_caps_confidence_and_requires_review(self) -> None:
        candidate = gm_pipeline.Candidate(
            sentence="The rejection caused concern.",
            span="rejection",
            start=4,
            end=13,
            rule_id="PROCESS_NOMINAL_GROUP",
            family="ideational",
            remapping_hint="PROCESS_TO_THING",
            language="en",
        )
        for mismatch in (True, False):
            analysis = gm_pipeline.SemanticAnalysis(
                context_sufficiency="PARTIAL",
                mapping_mismatch=mismatch,
                congruent_agnate_plausible=True,
                remapping_explicit=True,
                lexical_only=False,
                congruent_agnate="Someone rejected something.",
            )
            decision = gm_pipeline.ConservativeGMDecisionEngine().decide(
                candidate, analysis
            )
            self.assertNotEqual(decision.confidence, "HIGH")
            self.assertTrue(decision.needs_human_review)

    def test_invalid_context_value_is_indeterminate(self) -> None:
        candidate = gm_pipeline.Candidate(
            sentence="development",
            span="development",
            start=0,
            end=11,
            rule_id="PROCESS_NOMINAL_GROUP",
            family="ideational",
            remapping_hint="PROCESS_TO_THING",
            language="en",
        )
        decision = gm_pipeline.ConservativeGMDecisionEngine().decide(
            candidate,
            gm_pipeline.SemanticAnalysis(context_sufficiency="UNKNOWN"),
        )
        self.assertEqual(decision.ideational_gm_status, "INDETERMINATE")
        self.assertEqual(decision.confidence, "LOW")
        self.assertTrue(decision.needs_human_review)

    def test_annotation_validator_interface(self) -> None:
        _, records = load_gold()
        record = next(item for item in records if item["sentence_id"] == "en-002")
        self.assertEqual(gm_pipeline.AnnotationValidator().validate(record), [])


if __name__ == "__main__":
    unittest.main()
