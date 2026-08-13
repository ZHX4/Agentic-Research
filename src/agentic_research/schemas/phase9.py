"""Phase 9 autonomous discovery contracts."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


RunStatus = Literal["planned", "running", "paused", "completed", "failed", "cancelled"]
StageName = Literal["gap", "verify", "hypothesis", "execute", "evaluate", "review", "report"]
StageStatus = Literal["pending", "running", "succeeded", "failed", "skipped"]
ReviewSeverity = Literal["info", "warning", "critical"]
ReviewDecision = Literal["accept", "revise", "reject", "inconclusive"]


class AutonomousRunConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_iterations: int = Field(default=5, ge=1, le=100)
    max_stage_retries: int = Field(default=1, ge=0, le=10)
    checkpoint_every_stage: bool = True
    stop_on_critical_review: bool = True
    stop_on_no_progress: bool = True
    no_progress_patience: int = Field(default=2, ge=1, le=20)
    require_phase8_evaluation: bool = True
    require_review_before_next_iteration: bool = True


class StageExecution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage_id: str = Field(min_length=1)
    iteration: int = Field(ge=0)
    stage: StageName
    status: StageStatus
    input_artifact: str | None = None
    output_artifact: str | None = None
    input_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    output_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    attempts: int = Field(default=0, ge=0)
    error: str | None = None


class Checkpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    checkpoint_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    iteration: int = Field(ge=0)
    last_completed_stage: StageName | None = None
    state_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    created_at: str = Field(min_length=1)


class ReviewerFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(min_length=1)
    reviewer_id: str = Field(min_length=1)
    target_kind: Literal["gap", "verification", "hypothesis", "execution", "evaluation", "run"]
    target_id: str = Field(min_length=1)
    severity: ReviewSeverity
    decision: ReviewDecision
    claim: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)


class ReviewRound(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_id: str = Field(min_length=1)
    iteration: int = Field(ge=0)
    findings: list[ReviewerFinding] = Field(default_factory=list)
    consensus: ReviewDecision
    critical_count: int = Field(ge=0)
    reviewer_count: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_counts(self) -> "ReviewRound":
        actual = sum(1 for item in self.findings if item.severity == "critical")
        if actual != self.critical_count:
            raise ValueError("critical_count must equal the number of critical findings")
        reviewer_ids = {item.reviewer_id for item in self.findings}
        if reviewer_ids and len(reviewer_ids) > self.reviewer_count:
            raise ValueError("reviewer_count cannot be lower than distinct reviewers")
        return self


class AutonomousRunState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)
    status: RunStatus
    iteration: int = Field(ge=0)
    config: AutonomousRunConfig
    current_stage: StageName | None = None
    gap_ids: list[str] = Field(default_factory=list)
    verification_ids: list[str] = Field(default_factory=list)
    hypothesis_ids: list[str] = Field(default_factory=list)
    experiment_ids: list[str] = Field(default_factory=list)
    evaluation_ids: list[str] = Field(default_factory=list)
    stage_executions: list[StageExecution] = Field(default_factory=list)
    checkpoints: list[Checkpoint] = Field(default_factory=list)
    reviews: list[ReviewRound] = Field(default_factory=list)
    progress_signatures: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    stop_reason: str | None = None

    @model_validator(mode="after")
    def validate_state(self) -> "AutonomousRunState":
        if self.status == "completed" and self.current_stage is not None:
            raise ValueError("Completed runs must not have a current stage")
        if self.iteration > self.config.max_iterations:
            raise ValueError("iteration cannot exceed max_iterations")
        stage_ids = [item.stage_id for item in self.stage_executions]
        if len(stage_ids) != len(set(stage_ids)):
            raise ValueError("stage_id values must be unique")
        checkpoint_ids = [item.checkpoint_id for item in self.checkpoints]
        if len(checkpoint_ids) != len(set(checkpoint_ids)):
            raise ValueError("checkpoint_id values must be unique")
        return self


class AutonomousRunReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    final_status: RunStatus
    iterations_completed: int = Field(ge=0)
    stage_count: int = Field(ge=0)
    review_count: int = Field(ge=0)
    critical_findings: int = Field(ge=0)
    provenance_refs: list[str] = Field(default_factory=list)
    output_artifacts: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    stop_reason: str | None = None
