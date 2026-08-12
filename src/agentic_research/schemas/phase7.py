"""Phase 7 scientific execution contracts."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ExecutionStatus = Literal["planned", "running", "succeeded", "failed", "timeout", "rejected", "cancelled"]


class DatasetManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    source: str = Field(min_length=1)
    uri: str | None = None
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    license: str | None = None
    immutable: bool = True
    local_path: str | None = None


class FalsificationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str = Field(min_length=1)
    hypothesis_id: str = Field(min_length=1)
    primary_metric: str = Field(min_length=1)
    null_hypothesis: str = Field(min_length=1)
    rejection_criteria: list[str] = Field(min_length=1)
    required_ablations: list[str] = Field(default_factory=list)
    required_controls: list[str] = Field(default_factory=list)
    minimum_effect_size: float | None = Field(default=None, ge=0)
    alpha: float = Field(default=0.05, gt=0, lt=1)
    confidence_level: float = Field(default=0.95, gt=0, lt=1)


class SandboxPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image: str = Field(min_length=1)
    network_enabled: bool = False
    read_only_root: bool = True
    memory_mb: int = Field(default=4096, ge=256, le=65536)
    cpu_count: float = Field(default=2.0, gt=0, le=64)
    timeout_seconds: int = Field(default=3600, ge=1, le=86400)
    pids_limit: int = Field(default=256, ge=16, le=4096)
    workdir: str = "/workspace"
    allow_gpu: bool = False
    allowed_env: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_policy(self) -> "SandboxPolicy":
        if self.network_enabled and self.allow_gpu:
            raise ValueError("network_enabled and allow_gpu cannot both be true by default")
        if not self.read_only_root and self.workdir == "/workspace":
            raise ValueError("workdir must be explicit when read_only_root is false")
        return self


class ExperimentSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment_id: str = Field(min_length=1)
    hypothesis_id: str = Field(min_length=1)
    research_question: str = Field(min_length=1)
    command: list[str] = Field(min_length=1)
    code_path: str = Field(min_length=1)
    code_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    datasets: list[DatasetManifest] = Field(default_factory=list)
    baselines: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(min_length=1)
    seeds: list[int] = Field(min_length=1)
    falsification: FalsificationPlan
    sandbox: SandboxPolicy
    parameters: dict[str, str | int | float | bool] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_experiment(self) -> "ExperimentSpec":
        if len(set(self.seeds)) != len(self.seeds):
            raise ValueError("Experiment seeds must be unique")
        if any(seed < 0 for seed in self.seeds):
            raise ValueError("Experiment seeds must be non-negative")
        if self.falsification.hypothesis_id != self.hypothesis_id:
            raise ValueError("Falsification plan must target the same hypothesis")
        if Path(self.code_path).is_absolute() or ".." in Path(self.code_path).parts:
            raise ValueError("code_path must be relative and cannot escape the code directory")
        return self


class MetricRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    value: float
    seed: int
    split: str = Field(min_length=1)
    lower: float | None = None
    upper: float | None = None


class ArtifactRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(min_length=1)
    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_size: int = Field(ge=0)
    media_type: str = Field(min_length=1)


class SeedRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seed: int = Field(ge=0)
    status: ExecutionStatus
    exit_code: int | None = None
    duration_seconds: float = Field(ge=0)
    metrics: list[MetricRecord] = Field(default_factory=list)
    artifacts: list[ArtifactRecord] = Field(default_factory=list)
    stdout_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    stderr_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    error: str | None = None


class ExperimentResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str = Field(min_length=1)
    experiment_id: str = Field(min_length=1)
    hypothesis_id: str = Field(min_length=1)
    status: ExecutionStatus
    seed_runs: list[SeedRun] = Field(min_length=1)
    aggregate_metrics: list[MetricRecord] = Field(default_factory=list)
    falsified: bool | None = None
    falsification_rationale: str | None = None
    reproducible: bool | None = None
    environment_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    command_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    created_at: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_result(self) -> "ExperimentResult":
        if any(run.seed < 0 for run in self.seed_runs):
            raise ValueError("Seed runs must use non-negative seeds")
        statuses = {run.status for run in self.seed_runs}
        if self.status == "succeeded" and not statuses <= {"succeeded"}:
            raise ValueError("A succeeded experiment requires every seed run to succeed")
        if self.falsified is True and not self.falsification_rationale:
            raise ValueError("Falsified results require a rationale")
        return self


class ExperimentNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(min_length=1)
    experiment_id: str = Field(min_length=1)
    parent_node_id: str | None = None
    generation: int = Field(ge=0)
    relation: Literal["initial", "mutation", "ablation", "replication", "branch"]
    status: ExecutionStatus
    result_id: str | None = None


class ExperimentSearchTree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tree_id: str = Field(min_length=1)
    hypothesis_id: str = Field(min_length=1)
    root_experiment_id: str = Field(min_length=1)
    nodes: list[ExperimentNode] = Field(min_length=1)
    terminal_node_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_tree(self) -> "ExperimentSearchTree":
        ids = {node.node_id for node in self.nodes}
        if len(ids) != len(self.nodes):
            raise ValueError("Experiment tree node IDs must be unique")
        for node in self.nodes:
            if node.parent_node_id is not None and node.parent_node_id not in ids:
                raise ValueError("Experiment tree parent must reference an existing node")
        if not set(self.terminal_node_ids) <= ids:
            raise ValueError("Terminal nodes must reference tree nodes")
        return self
