"""Adversarial candidate-gap and novelty verification (Phase 5)."""

from .devils_advocate import DevilsAdvocateAgent
from .novelty import NoveltyVerifier

__all__ = ["NoveltyVerifier", "DevilsAdvocateAgent"]
