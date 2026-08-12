"""Hypothesis and experimental-plan contracts."""

from pydantic import BaseModel, ConfigDict, Field


class Hypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hypothesis_id: str
    statement: str
    source_gap_ids: list[str] = Field(default_factory=list)
    novelty_score: float = Field(ge=0, le=1)
    evidence_score: float = Field(ge=0, le=1)
    significance_score: float = Field(ge=0, le=1)
    feasibility_score: float = Field(ge=0, le=1)
    diversity_score: float = Field(ge=0, le=1)
    falsification_condition: str

    @property
    def composite_score(self) -> float:
        return (
            0.25 * self.novelty_score
            + 0.20 * self.evidence_score
            + 0.20 * self.significance_score
            + 0.20 * self.feasibility_score
            + 0.15 * self.diversity_score
        )


class ExperimentPlan(BaseModel):
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
