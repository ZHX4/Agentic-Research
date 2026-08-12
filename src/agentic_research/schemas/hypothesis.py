"""Backward-compatible hypothesis schema exports."""
from pydantic import BaseModel, ConfigDict, Field

from .phase6 import Hypothesis, HypothesisCandidate, HypothesisConfig, HypothesisReflection, HypothesisRun


class ExperimentPlan(BaseModel):
    """Legacy experiment-plan contract retained for later Phase 7 use."""
    model_config = ConfigDict(extra="forbid")
    hypothesis_id: str
    research_question: str
    datasets: list[str] = Field(default_factory=list)
    baselines: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    seeds: list[int] = Field(default_factory=lambda: [1, 2, 3])
    ablations: list[str] = Field(default_factory=list)
    rejection_criteria: list[str] = Field(default_factory=list)
    compute_budget_hours: float = Field(default=1.0, gt=0)


__all__ = ["Hypothesis", "HypothesisCandidate", "HypothesisConfig", "HypothesisReflection", "HypothesisRun", "ExperimentPlan"]
