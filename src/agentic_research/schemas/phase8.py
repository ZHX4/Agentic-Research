"""Phase 8 evaluation and benchmarking contracts."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

BenchmarkKind = Literal["retrieval", "extraction", "gap", "novelty", "temporal", "human", "baseline", "ablation"]
MetricDirection = Literal["higher", "lower"]


class BenchmarkCase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str = Field(min_length=1)
    kind: BenchmarkKind
    input_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_ids: list[str] = Field(default_factory=list)
    expected_labels: list[str] = Field(default_factory=list)
    expected_fields: dict[str, str] = Field(default_factory=dict)
    publication_year: int | None = Field(default=None, ge=1900, le=2200)
    cutoff_year: int | None = Field(default=None, ge=1900, le=2200)
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_temporal(self) -> "BenchmarkCase":
        if self.kind == "temporal" and self.cutoff_year is None:
            raise ValueError("Temporal benchmark cases require cutoff_year")
        return self


class PredictionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str = Field(min_length=1)
    predicted_ids: list[str] = Field(default_factory=list)
    predicted_labels: list[str] = Field(default_factory=list)
    extracted_fields: dict[str, str] = Field(default_factory=dict)
    scores: dict[str, float] = Field(default_factory=dict)
    publication_years: dict[str, int | None] = Field(default_factory=dict)
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)


class MetricValue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1)
    value: float
    direction: MetricDirection = "higher"
    unit: str = "score"
    numerator: float | None = None
    denominator: float | None = None
    n: int | None = Field(default=None, ge=0)
    details: dict[str, float | int | str | bool] = Field(default_factory=dict)


class BenchmarkResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str = Field(min_length=1)
    benchmark_id: str = Field(min_length=1)
    kind: BenchmarkKind
    system_name: str = Field(min_length=1)
    split: Literal["dev", "test", "temporal_test"]
    metrics: list[MetricValue] = Field(default_factory=list)
    cases_evaluated: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)


class HumanRating(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str = Field(min_length=1)
    annotator_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    score: float | None = None
    rationale: str | None = None


class HumanEvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evaluation_id: str = Field(min_length=1)
    task: Literal["gap_quality", "novelty_verdict", "extraction_quality", "hypothesis_quality"]
    annotator_count: int = Field(ge=2)
    item_count: int = Field(ge=0)
    agreement_metrics: list[MetricValue] = Field(default_factory=list)
    aggregate_scores: list[MetricValue] = Field(default_factory=list)
    ratings: list[HumanRating] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_raters(self) -> "HumanEvaluationResult":
        annotators = {rating.annotator_id for rating in self.ratings}
        if len(annotators) != self.annotator_count:
            raise ValueError("annotator_count must match ratings exactly")
        if len(self.ratings) < self.item_count * 2:
            raise ValueError("Human evaluation requires at least two ratings per evaluated item")
        return self


class BaselineSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    baseline_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    system_type: Literal["retrieval", "rag", "llm", "heuristic", "oracle"]
    command: list[str] = Field(min_length=1)
    config_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    notes: str | None = None


class BaselineComparison(BaseModel):
    model_config = ConfigDict(extra="forbid")
    comparison_id: str = Field(min_length=1)
    metric_name: str = Field(min_length=1)
    metric_direction: MetricDirection = "higher"
    primary_system: str = Field(min_length=1)
    baselines: list[str] = Field(min_length=1)
    metrics: dict[str, float] = Field(min_length=1)
    deltas: dict[str, float] = Field(default_factory=dict)
    winner: str | None = None
    warnings: list[str] = Field(default_factory=list)


class AblationSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ablation_id: str = Field(min_length=1)
    component: str = Field(min_length=1)
    enabled: bool
    config_overrides: dict[str, str | int | float | bool] = Field(default_factory=dict)
    matched_case_ids: list[str] = Field(min_length=1)


class AblationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ablation_id: str = Field(min_length=1)
    component: str = Field(min_length=1)
    baseline_metrics: dict[str, float] = Field(min_length=1)
    ablated_metrics: dict[str, float] = Field(min_length=1)
    deltas: dict[str, float] = Field(default_factory=dict)
    relative_deltas: dict[str, float] = Field(default_factory=dict)


class CostRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str = Field(min_length=1)
    wall_seconds: float = Field(ge=0)
    cpu_seconds: float | None = Field(default=None, ge=0)
    gpu_seconds: float | None = Field(default=None, ge=0)
    peak_memory_mb: float | None = Field(default=None, ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)
    details: dict[str, float | int | str] = Field(default_factory=dict)


class EvaluationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    report_id: str = Field(min_length=1)
    system_name: str = Field(min_length=1)
    benchmark_results: list[BenchmarkResult] = Field(default_factory=list)
    human_evaluations: list[HumanEvaluationResult] = Field(default_factory=list)
    baseline_comparisons: list[BaselineComparison] = Field(default_factory=list)
    ablations: list[AblationResult] = Field(default_factory=list)
    costs: list[CostRecord] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_runs(self) -> "EvaluationReport":
        ids = [item.run_id for item in self.benchmark_results]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate benchmark run IDs are not allowed")
        return self
