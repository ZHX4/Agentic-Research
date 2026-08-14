"""Independent, provider-neutral reviewers for autonomous research runs."""
from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from typing import Any

from agentic_research.schemas.phase9 import ReviewDecision, ReviewRound, ReviewerFinding


class Reviewer(ABC):
    reviewer_id: str

    @abstractmethod
    def review(self, iteration: int, target_kind: str, target_id: str, artifact: dict[str, Any]) -> ReviewerFinding:
        raise NotImplementedError


def _finding_id(reviewer_id: str, iteration: int, target_id: str) -> str:
    return f"finding:{reviewer_id}:{iteration}:{hashlib.sha1(target_id.encode()).hexdigest()[:16]}"


class ProvenanceReviewer(Reviewer):
    reviewer_id = "reviewer-provenance-v1"

    def review(self, iteration: int, target_kind: str, target_id: str, artifact: dict[str, Any]) -> ReviewerFinding:
        refs = artifact.get("provenance_refs")
        warnings: list[str] = []
        if not isinstance(refs, list) or not refs:
            warnings.append("Artifact contains no provenance references.")
        if artifact.get("output_sha256") is None and target_kind in {"execution", "evaluation"}:
            warnings.append("Execution/evaluation artifact has no output hash reference.")
        if warnings:
            decision: ReviewDecision = "reject" if any("no provenance" in item.lower() for item in warnings) else "revise"
            severity = "critical" if decision == "reject" else "warning"
        else:
            decision = "accept"
            severity = "info"
        digest = hashlib.sha256(repr(sorted(artifact.items())).encode("utf-8")).hexdigest()[:16]
        return ReviewerFinding(
            finding_id=_finding_id(self.reviewer_id, iteration, target_id), reviewer_id=self.reviewer_id,
            target_kind=target_kind, target_id=target_id, severity=severity, decision=decision,
            claim="Provenance and artifact-integrity requirements are satisfied." if decision == "accept" else "Provenance requirements are incomplete.",
            rationale="; ".join(warnings) if warnings else "Provenance references and required artifact-integrity fields are present.",
            evidence_refs=[f"review-input:{digest}"],
        )


class ScientificIntegrityReviewer(Reviewer):
    reviewer_id = "reviewer-scientific-integrity-v1"

    def review(self, iteration: int, target_kind: str, target_id: str, artifact: dict[str, Any]) -> ReviewerFinding:
        warnings: list[str] = []
        if target_kind == "execution" and artifact.get("status") in {"failed", "timeout", "rejected", "cancelled"}:
            warnings.append(f"Execution status is {artifact.get('status')}.")
        if target_kind == "evaluation" and artifact.get("cases_evaluated") == 0:
            warnings.append("Evaluation contains zero evaluated cases.")
        if target_kind == "hypothesis" and not artifact.get("falsification_condition"):
            warnings.append("Hypothesis lacks an explicit falsification condition.")
        if artifact.get("global_novelty") is True:
            warnings.append("Autonomous loop must not claim global novelty in Phase 9.")
        if warnings:
            decision: ReviewDecision = "reject" if any("global novelty" in item.lower() for item in warnings) else "revise"
            severity = "critical" if decision == "reject" else "warning"
        else:
            decision = "accept"
            severity = "info"
        digest = hashlib.sha256(repr(sorted(artifact.items())).encode("utf-8")).hexdigest()[:16]
        return ReviewerFinding(
            finding_id=_finding_id(self.reviewer_id, iteration, target_id), reviewer_id=self.reviewer_id,
            target_kind=target_kind, target_id=target_id, severity=severity, decision=decision,
            claim="Scientific-integrity constraints pass." if decision == "accept" else "Scientific-integrity review requires corrective action.",
            rationale="; ".join(warnings) if warnings else "No prohibited scientific conclusion or missing control was detected structurally.",
            evidence_refs=[f"review-input:{digest}"],
        )


class DeterministicReviewer(ProvenanceReviewer):
    """Backward-compatible deterministic reviewer used by offline tests."""


class ReviewPanel:
    def __init__(self, reviewers: list[Reviewer]) -> None:
        if not reviewers:
            raise ValueError("At least one reviewer is required")
        ids = [reviewer.reviewer_id for reviewer in reviewers]
        if len(ids) != len(set(ids)):
            raise ValueError("Reviewer IDs must be unique")
        self.reviewers = reviewers

    def review(self, iteration: int, target_kind: str, target_id: str, artifact: dict[str, Any]) -> ReviewRound:
        findings = [reviewer.review(iteration, target_kind, target_id, artifact) for reviewer in self.reviewers]
        critical = sum(1 for finding in findings if finding.severity == "critical")
        rejects = sum(1 for finding in findings if finding.decision == "reject")
        revisions = sum(1 for finding in findings if finding.decision == "revise")
        if rejects > len(findings) / 2:
            consensus: ReviewDecision = "reject"
        elif rejects or revisions:
            consensus = "revise"
        elif all(finding.decision == "accept" for finding in findings):
            consensus = "accept"
        else:
            consensus = "inconclusive"
        return ReviewRound(
            review_id=f"review:{iteration}:{target_kind}:{target_id}", iteration=iteration, findings=findings,
            consensus=consensus, critical_count=critical, reviewer_count=len(self.reviewers),
        )
