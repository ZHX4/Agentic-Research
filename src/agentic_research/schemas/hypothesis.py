"""Backward-compatible Phase 6 hypothesis schema exports.

The canonical hypothesis model lives in :mod:`agentic_research.schemas.phase6`.
"""

from .phase6 import Hypothesis, HypothesisCandidate, HypothesisConfig, HypothesisReflection, HypothesisRun
from .hypothesis import ExperimentPlan as _LegacyExperimentPlan

ExperimentPlan = _LegacyExperimentPlan

__all__ = ["Hypothesis", "HypothesisCandidate", "HypothesisConfig", "HypothesisReflection", "HypothesisRun", "ExperimentPlan"]
