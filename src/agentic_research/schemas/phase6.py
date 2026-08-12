"""Phase 6 hypothesis-reasoning contracts."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .gap import GapStatus

HypothesisOrigin = Literal["gap_direct", "gap_composed", "gap_conservative", "gap_high_risk", "evolved"]


class Hypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    hypothesis_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    research_question: str = Field(min_length=1)
    source_gap_ids: list[str] = Field(default_factory=list)
    source_statuses: list[GapStatus] = Field(default_factory=list)
    origin: HypothesisOrigin
    mechanism: str = Field(min_length=1)
    expected_effect: str = Field(min_length=1)
    falsification_condition: str = Field(min_length=1)
    assumptions: list[str] = Field(default_factory=list)
    predicted_observations: list[str] = Field(default_factory=list)
    novelty_score: float = Field(ge=0, le=1)
    evidence_score: float = Field(ge=0, le=1)
    significance_score: float = Field(ge=0, le=1)
    feasibility_score: float = Field(ge=0, le=1)
    diversity_score: float = Field(ge=0, le=1)
    robustness_score: float = Field(ge=0, le=1)
    reflection_score: float = Field(ge=0, le=1)

    @property
    def composite_score(self) -> float:
        return 0.22 * self.novelty_score + 0.16 * self.evidence_score + 0.17 * self.significance_score + 0.17 * self.feasibility_score + 0.10 * self.diversity_score + 0.10 * self.robustness_score + 0.08 * self.reflection_score


class HypothesisReflection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reflection_id: str = Field(min_length=1)
    hypothesis_id: str = Field(min_length=1)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    hidden_assumptions: list[str] = Field(default_factory=list)
    confounders: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
    score: float = Field(ge=0, le=1)
    recommendation: Literal["advance", "revise", "discard"]


class HypothesisCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    hypothesis: Hypothesis
    reflection: HypothesisReflection


class HypothesisConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    hypotheses_per_gap: int = Field(default=6, ge=1, le=50)
    max_composed_pairs: int = Field(default=25, ge=0, le=200)
    dedup_similarity_threshold: float = Field(default=0.82, ge=0, le=1)
    tournament_size: int = Field(default=5, ge=2, le=20)
    tournament_rounds: int = Field(default=3, ge=1, le=20)
    pareto_limit: int = Field(default=12, ge=1, le=100)
    keep_diverse_limit: int = Field(default=20, ge=1, le=200)
    evolve_top_k: int = Field(default=6, ge=1, le=50)
    max_evolution_generations: int = Field(default=2, ge=0, le=10)
    min_gap_status: GapStatus = GapStatus.SURVIVED
    allow_uncertain_gaps: bool = False
    clustering_threshold: float = Field(default=0.70, ge=0, le=1)

    @model_validator(mode="after")
    def validate_limits(self) -> "HypothesisConfig":
        if self.evolve_top_k > self.keep_diverse_limit:
            raise ValueError("evolve_top_k cannot exceed keep_diverse_limit")
        return self


class HypothesisRun(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str = Field(min_length=1)
    input_gap_ids: list[str] = Field(default_factory=list)
    initial_generated_count: int = Field(ge=0)
    evolved_count: int = Field(ge=0)
    generated_count: int = Field(ge=0)
    reflected_count: int = Field(ge=0)
    selected_count: int = Field(ge=0)
    pareto_count: int = Field(ge=0)
    cluster_count: int = Field(ge=0)
    candidates: list[HypothesisCandidate] = Field(default_factory=list)
    pareto_frontier_ids: list[str] = Field(default_factory=list)
    selected_hypothesis_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_integrity(self) -> "HypothesisRun":
        ids = [item.hypothesis.hypothesis_id for item in self.candidates]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate hypothesis IDs are not allowed")
        if self.generated_count != len(self.candidates):
            raise ValueError("generated_count must equal total candidate count")
        if self.initial_generated_count + self.evolved_count != self.generated_count:
            raise ValueError("initial_generated_count + evolved_count must equal generated_count")
        candidate_ids = set(ids)
        if not set(self.pareto_frontier_ids) <= candidate_ids:
            raise ValueError("Pareto frontier IDs must refer to candidates")
        if not set(self.selected_hypothesis_ids) <= candidate_ids:
            raise ValueError("Selected IDs must refer to candidates")
        return self
