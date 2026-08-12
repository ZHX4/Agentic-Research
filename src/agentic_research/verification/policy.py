"""Scientific decision policy layered on top of the Phase 5 search engine."""

from __future__ import annotations

from agentic_research.schemas.gap import GapCandidate, GapStatus
from agentic_research.schemas.phase5 import GapVerificationResult, NoveltyVerificationConfig
from agentic_research.verification.novelty import NoveltyVerifier


class AdversarialNoveltyVerifier(NoveltyVerifier):
    """Apply conservative decision rules to the Phase 5 retrieval evidence."""

    def verify(self, candidate: GapCandidate, config: NoveltyVerificationConfig | None = None) -> GapVerificationResult:
        result = super().verify(candidate, config)
        if any(match.exact_combination for match in result.prior_work):
            confidence = min(0.99, max(result.confidence, 0.95))
            status = GapStatus.DISPROVED if (config or NoveltyVerificationConfig()).allow_status_transition else GapStatus.CANDIDATE
            verified = result.verified_candidate.model_copy(update={"status": status, "confidence": confidence})
            return result.model_copy(
                update={
                    "verdict": "disproved",
                    "resulting_status": status,
                    "confidence": confidence,
                    "rationale": "A retrieved prior paper directly contains the candidate method/dataset/task combination; title or abstract wording cannot override that direct match.",
                    "verified_candidate": verified,
                }
            )
        return result
