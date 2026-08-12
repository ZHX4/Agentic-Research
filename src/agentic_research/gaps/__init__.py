"""Candidate gap discovery algorithms."""

from .detector import detect_missing_combinations
from .discovery import discover_gaps

__all__ = ["detect_missing_combinations", "discover_gaps"]
