#!/usr/bin/env python3
"""Lightweight extension points for conservative GM candidate analysis.

This module deliberately separates surface candidate extraction from semantic
decision.  A regular-expression hit never becomes grammatical metaphor until
cross-stratal mapping evidence and a plausible congruent agnate are supplied.
"""

from __future__ import annotations

import argparse
import json
import re
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_RULES = SCRIPT_DIR.parent / "references" / "gm-candidate-rules.yaml"


@dataclass(frozen=True)
class Candidate:
    """A span nominated for analysis, not a GM verdict."""

    sentence: str
    span: str
    start: int
    end: int
    rule_id: str
    family: str
    remapping_hint: str
    language: str


@dataclass(frozen=True)
class SemanticAnalysis:
    """Evidence required before a candidate can be classified."""

    context_sufficiency: str = "INSUFFICIENT"
    mapping_mismatch: bool | None = None
    congruent_agnate_plausible: bool | None = None
    remapping_explicit: bool | None = None
    lexical_only: bool | None = None
    congruent_agnate: str | None = None
    positive_evidence: tuple[str, ...] = ()
    counter_evidence: tuple[str, ...] = ()
    blocking_counter_evidence: bool = False


@dataclass(frozen=True)
class GMDecision:
    gm_candidate: bool
    ideational_gm_status: str
    interpersonal_gm_status: str
    confidence: str
    needs_human_review: bool
    rationale: tuple[str, ...] = field(default_factory=tuple)


class CandidateExtractor(ABC):
    """Nominate auditable spans; never assign a GM label."""

    @abstractmethod
    def extract(self, sentence: str, language: str) -> list[Candidate]:
        raise NotImplementedError


class SemanticAnalyzer(ABC):
    """Establish contextual meaning and the semantics/grammar mapping."""

    @abstractmethod
    def analyze(self, candidate: Candidate, context: Mapping[str, str]) -> SemanticAnalysis:
        raise NotImplementedError


class CongruentAgnateGenerator(ABC):
    """Propose a natural, meaning-matched agnate without forcing one."""

    @abstractmethod
    def generate(
        self, candidate: Candidate, analysis: SemanticAnalysis
    ) -> str | None:
        raise NotImplementedError


class GMDecisionEngine(ABC):
    """Apply the explicit evidence formula and uncertainty gates."""

    @abstractmethod
    def decide(self, candidate: Candidate, analysis: SemanticAnalysis) -> GMDecision:
        raise NotImplementedError


class AnnotationValidator:
    """Stable wrapper around the v2/v3 validator for future pipeline stages."""

    def __init__(self) -> None:
        import validate_gm_annotation

        self._validator = validate_gm_annotation
        self._schemas = {
            version: validate_gm_annotation.load_schema(path)
            for version, path in validate_gm_annotation.SCHEMA_PATHS.items()
        }
        self._candidate_rule_ids = validate_gm_annotation.load_candidate_rule_ids()

    def validate(self, record: Mapping[str, Any], label: str = "record") -> list[str]:
        return self._validator.validate_record(
            dict(record),
            label=label,
            schemas=self._schemas,
            candidate_rule_ids=self._candidate_rule_ids,
        )


def load_rules(path: Path = DEFAULT_RULES) -> list[dict[str, Any]]:
    """Load JSON-compatible YAML without adding a YAML runtime dependency."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load candidate rules {path}: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("rules"), list):
        raise ValueError("candidate rule file must contain a rules array")
    rules: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, rule in enumerate(payload["rules"]):
        if not isinstance(rule, dict):
            raise ValueError(f"candidate rule {index} must be an object")
        rule_id = rule.get("id")
        if not isinstance(rule_id, str) or not rule_id or rule_id in seen:
            raise ValueError(f"candidate rule {index} has a missing or duplicate id")
        seen.add(rule_id)
        patterns = rule.get("patterns")
        languages = rule.get("languages")
        if not isinstance(patterns, list) or not all(
            isinstance(pattern, str) for pattern in patterns
        ):
            raise ValueError(f"candidate rule {rule_id} has invalid patterns")
        if not isinstance(languages, list) or not all(
            language in {"en", "zh", "other"} for language in languages
        ):
            raise ValueError(f"candidate rule {rule_id} has invalid languages")
        for pattern in patterns:
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ValueError(f"candidate rule {rule_id} has invalid regex: {exc}") from exc
        rules.append(rule)
    return rules


class RuleCandidateExtractor(CandidateExtractor):
    """A transparent high-recall baseline driven by the external rule file."""

    def __init__(self, rules_path: Path = DEFAULT_RULES) -> None:
        self.rules = load_rules(rules_path)

    def extract(self, sentence: str, language: str) -> list[Candidate]:
        if language not in {"en", "zh", "other"}:
            raise ValueError(f"unsupported language: {language}")
        candidates: list[Candidate] = []
        seen: set[tuple[int, int, str]] = set()
        for rule in self.rules:
            if language not in rule["languages"]:
                continue
            for pattern in rule["patterns"]:
                for match in re.finditer(pattern, sentence, flags=re.IGNORECASE):
                    identity = (match.start(), match.end(), rule["id"])
                    if identity in seen:
                        continue
                    seen.add(identity)
                    candidates.append(
                        Candidate(
                            sentence=sentence,
                            span=match.group(0),
                            start=match.start(),
                            end=match.end(),
                            rule_id=rule["id"],
                            family=str(rule.get("candidate_family", "unknown")),
                            remapping_hint=str(rule.get("remapping_hint", "NONE")),
                            language=language,
                        )
                    )
        return sorted(candidates, key=lambda item: (item.start, item.end, item.rule_id))


class UnresolvedSemanticAnalyzer(SemanticAnalyzer):
    """Safe default: surface evidence remains unresolved until context is supplied."""

    def analyze(self, candidate: Candidate, context: Mapping[str, str]) -> SemanticAnalysis:
        before = context.get("context_before", "")
        after = context.get("context_after", "")
        sufficiency = "PARTIAL" if before or after else "INSUFFICIENT"
        return SemanticAnalysis(
            context_sufficiency=sufficiency,
            positive_evidence=(f"surface candidate from rule {candidate.rule_id}",),
            counter_evidence=("cross-stratal mapping has not yet been established",),
        )


class ProvidedAgnateGenerator(CongruentAgnateGenerator):
    """Return a reviewed agnate; never synthesize one from a suffix alone."""

    def generate(
        self, candidate: Candidate, analysis: SemanticAnalysis
    ) -> str | None:
        del candidate
        if analysis.congruent_agnate_plausible is True:
            return analysis.congruent_agnate
        return None


class ConservativeGMDecisionEngine(GMDecisionEngine):
    """Small deterministic baseline that implements the published v3 formula."""

    def decide(self, candidate: Candidate, analysis: SemanticAnalysis) -> GMDecision:
        if analysis.context_sufficiency not in ("SUFFICIENT", "PARTIAL", "INSUFFICIENT"):
            return GMDecision(
                gm_candidate=False,
                ideational_gm_status="INDETERMINATE",
                interpersonal_gm_status="INDETERMINATE",
                confidence="LOW",
                needs_human_review=True,
                rationale=("context sufficiency is invalid or unresolved",),
            )
        if analysis.context_sufficiency == "INSUFFICIENT":
            return GMDecision(
                gm_candidate=False,
                ideational_gm_status="INDETERMINATE",
                interpersonal_gm_status="INDETERMINATE",
                confidence="LOW",
                needs_human_review=True,
                rationale=("context gate: only conditional interpretations are licensed",),
            )

        if analysis.lexical_only is True:
            return GMDecision(
                gm_candidate=False,
                ideational_gm_status="NON_GM",
                interpersonal_gm_status="NON_GM",
                confidence="HIGH" if analysis.context_sufficiency == "SUFFICIENT" else "MEDIUM",
                needs_human_review=analysis.context_sufficiency != "SUFFICIENT",
                rationale=("the evidence is lexical only, so the GM formula is false",),
            )

        predicates = (
            analysis.mapping_mismatch,
            analysis.congruent_agnate_plausible,
            analysis.remapping_explicit,
            analysis.lexical_only,
        )
        unresolved = any(value is None for value in predicates)
        gm_candidate = (
            analysis.mapping_mismatch is True
            and analysis.congruent_agnate_plausible is True
            and analysis.remapping_explicit is True
            and analysis.lexical_only is False
        )
        if unresolved:
            return GMDecision(
                gm_candidate=False,
                ideational_gm_status="INDETERMINATE",
                interpersonal_gm_status="INDETERMINATE",
                confidence="LOW",
                needs_human_review=True,
                rationale=("one or more cross-stratal decision predicates are unresolved",),
            )
        if gm_candidate:
            status = "MARGINAL_GM" if analysis.blocking_counter_evidence else "TYPICAL_GM"
            partial = analysis.context_sufficiency == "PARTIAL"
            confidence = "MEDIUM" if analysis.blocking_counter_evidence or partial else "HIGH"
            interpersonal = candidate.family in {"interpersonal", "polarity"}
            return GMDecision(
                gm_candidate=True,
                ideational_gm_status="NON_GM" if interpersonal else status,
                interpersonal_gm_status=status if interpersonal else "NON_GM",
                confidence=confidence,
                needs_human_review=analysis.blocking_counter_evidence or partial,
                rationale=(
                    "mapping mismatch, plausible agnate, and explicit remapping are present",
                    "lexical-only analysis is excluded",
                ),
            )
        if analysis.congruent_agnate_plausible is False and analysis.mapping_mismatch is True:
            return GMDecision(
                gm_candidate=False,
                ideational_gm_status="MARGINAL_GM",
                interpersonal_gm_status="NON_GM",
                confidence="MEDIUM",
                needs_human_review=True,
                rationale=("candidate signal lacks a defensible congruent agnate",),
            )
        return GMDecision(
            gm_candidate=False,
            ideational_gm_status="NON_GM",
            interpersonal_gm_status="NON_GM",
            confidence=(
                "MEDIUM" if analysis.context_sufficiency == "PARTIAL" else "HIGH"
            ),
            needs_human_review=analysis.context_sufficiency == "PARTIAL",
            rationale=("the complete GM-candidate relation is not established",),
        )


def candidates_as_json(
    extractor: CandidateExtractor, sentence: str, language: str
) -> Iterable[str]:
    for candidate in extractor.extract(sentence, language):
        yield json.dumps(asdict(candidate), ensure_ascii=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sentence")
    parser.add_argument("--language", choices=("en", "zh", "other"), required=True)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    args = parser.parse_args(argv)
    extractor = RuleCandidateExtractor(args.rules)
    for line in candidates_as_json(extractor, args.sentence, args.language):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
