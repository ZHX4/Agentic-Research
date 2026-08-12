"""Structured Devil's Advocate agent for Phase 5."""

from __future__ import annotations

from agentic_research.schemas.gap import GapCandidate
from agentic_research.schemas.phase5 import GapVerificationResult, NoveltyVerificationConfig
from agentic_research.verification.novelty import NoveltyVerifier


class DevilsAdvocateAgent:
    """Adversarial agent whose objective is to disprove a candidate gap.

    The agent does not declare a gap globally novel. It delegates the evidence
    search to ``NoveltyVerifier`` and exposes the resulting attack record.
    """

    name = "devils-advocate"

    def __init__(self, verifier: NoveltyVerifier) -> None:
        self.verifier = verifier

    def challenge(self, candidate: GapCandidate, config: NoveltyVerificationConfig | None = None) -> GapVerificationResult:
        """Attempt to defeat one Phase 4 candidate using the configured search budget."""
        return self.verifier.verify(candidate, config)
