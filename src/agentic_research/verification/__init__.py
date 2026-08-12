"""Adversarial candidate-gap and novelty verification (Phase 5)."""

from .devils_advocate import DevilsAdvocateAgent
from .policy import AdversarialNoveltyVerifier

NoveltyVerifier = AdversarialNoveltyVerifier

__all__ = ["NoveltyVerifier", "AdversarialNoveltyVerifier", "DevilsAdvocateAgent"]
