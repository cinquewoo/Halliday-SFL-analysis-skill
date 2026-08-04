#!/usr/bin/env python3
"""Regression tests for skill routing, manifest UX, and bundled references."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_ROOT = SKILL_ROOT.parents[1]


class SkillContractTests(unittest.TestCase):
    def test_modes_are_explicit_and_explain_is_default(self) -> None:
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("**Explain is the default.**", text)
        self.assertIn("**explain**", text)
        self.assertIn("**annotate**", text)
        self.assertIn("**research**", text)
        self.assertIn("do **not** output full json by default", text.lower())
        self.assertNotIn("Output the v2 JSON object first", text)

    def test_markdown_reference_links_resolve(self) -> None:
        markdown_files = [SKILL_ROOT / "SKILL.md", *(SKILL_ROOT / "references").glob("*.md")]
        missing: list[str] = []
        for document in markdown_files:
            text = document.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                if "://" in target or target.startswith("#"):
                    continue
                path = (document.parent / target.split("#", 1)[0]).resolve()
                if not path.exists():
                    missing.append(f"{document.name}: {target}")
        self.assertEqual(missing, [])

    def test_schema_v3_contains_requested_core_fields_and_context_gate(self) -> None:
        schema = json.loads(
            (SKILL_ROOT / "references" / "gm-annotation-v3.schema.json").read_text(
                encoding="utf-8"
            )
        )
        required = set(schema["required"])
        expected = {
            "schema_version",
            "document_id",
            "sentence_id",
            "sentence",
            "context_before",
            "context_after",
            "candidate_span",
            "span_start",
            "span_end",
            "semantic_category",
            "actual_realization",
            "congruent_realization",
            "congruent_agnate",
            "remapping_type",
            "candidate_rule",
            "positive_evidence",
            "counter_evidence",
            "context_sufficiency",
            "confidence",
            "needs_human_review",
            "framework_profile",
            "operational_tests",
            "analyzer_version",
            "annotator_type",
            "source_provenance",
        }
        self.assertTrue(expected.issubset(required), expected - required)
        serialized = json.dumps(schema["allOf"], ensure_ascii=False)
        for invariant in (
            '"context_sufficiency": {"const": "INSUFFICIENT"}',
            '"ideational_gm_status": {"const": "INDETERMINATE"}',
            '"interpersonal_gm_status": {"const": "INDETERMINATE"}',
            '"confidence": {"const": "LOW"}',
            '"needs_human_review": {"const": true}',
        ):
            self.assertIn(invariant, serialized)

    def test_manifest_starter_prompts_follow_plugin_creator_limits(self) -> None:
        manifest = json.loads(
            (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        prompts = manifest["interface"]["defaultPrompt"]
        self.assertLessEqual(len(prompts), 3)
        self.assertTrue(all(len(prompt) <= 128 for prompt in prompts))
        self.assertRegex(manifest["version"], r"^1\.4\.0(?:\+codex\.\d{14})?$")


if __name__ == "__main__":
    unittest.main()
