"""Canonical scientific domain schemas."""

from .gap import GapCandidate, GapStatus
from .hypothesis import ExperimentPlan, Hypothesis
from .paper import Evidence, ExperimentResult, Paper

__all__ = [
    "Paper",
    "Evidence",
    "ExperimentResult",
    "GapCandidate",
    "GapStatus",
    "Hypothesis",
    "ExperimentPlan",
]
