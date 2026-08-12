"""Candidate research-gap discovery algorithms."""

from .detector import detect_missing_combinations
from .phase4_engine import discover_gaps

__all__ = ["detect_missing_combinations", "discover_gaps"]
