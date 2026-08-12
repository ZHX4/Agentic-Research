"""Canonical scientific domain schemas."""

from .paper import Paper, Evidence, ExperimentResult
from .gap import GapCandidate, GapStatus

__all__ = ["Paper", "Evidence", "ExperimentResult", "GapCandidate", "GapStatus"]
