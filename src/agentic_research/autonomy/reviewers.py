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


class DeterministicReviewer(Reviewer):
    """Conservative structural/provenance reviewer with no LLM dependency."""

    def __init__(self, reviewer_id: str, *, require_provenance: bool = True) -> None:
        self.reviewer_id = reviewer_id
        self.require_provenance = require_provenance

    def review(self, iteration: int, target_kind: str, target_id: str, artifact: dict[str, Any]) -> ReviewerFinding:
        warnings: list[str] = []
        evidence_refs: list[str] = []
        if self.require_provenance and not artifact.get("provenance_refs"):
            warnings.append("Missing provenance references")
        if artifact.get("status") in {"failed", "rejected", "cancelled"}:
            warnings.append(f"Artifact status is {artifact.get('status')}")
        if artifact.get("falsified") is False and artifact.get("falsification_rationale") is None and target_kind == "execution":
            warnings.append("Execution lacks an explicit falsification rationale")
        if artifact.get("warnings"):
            warnings.extend(str(item) for item in artifact["warnings"][:3])
        digest = hashlib.sha256(repr(sorted(artifact.items(), key=lambda item: item[0])).encode("utf-8")).hexdigest()
        evidence_refs.append(f"review-input:{digest[:16]}")
        if any("Missing provenance" in item for item in warnings):
            severity = "critical"
            decision: ReviewDecision = "reject"
        elif warnings:
            severity = "warning"
            decision = "revise"
        else:
            severity = "info"
            decision = "accept"
        claim = "Autonomous stage artifact passes structural review" if decision == "accept" else "Autonomous stage artifact requires review action"
        return ReviewerFinding(
            finding_id=f"finding:{self.reviewer_id}:{iteration}:{target_id}",
            reviewer_id=self.reviewer_id,
            target_kind=target_kind, target_id=target_id,
            severity=severity, decision=decision,
            claim=claim,
            rationale="; ".join(warnings) if warnings else "Required structural and provenance checks passed.",
            evidence_refs=evidence_refs,
        )


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
        if any(finding.decision == "reject" for finding in findings):
            consensus: ReviewDecision = "reject"
        elif any(finding.decision == "revise" for finding in findings):
            consensus = "revise"
        elif all(finding.decision == "accept" for finding in findings):
            consensus = "accept"
        else:
            consensus = "inconclusive"
        return ReviewRound(
            review_id=f"review:{iteration}:{target_id}", iteration=iteration,
            findings=findings, consensus=consensus, critical_count=critical,
            reviewer_count=len(self.reviewers),
        )
