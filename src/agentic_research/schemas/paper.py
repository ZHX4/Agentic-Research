"""Domain models for papers, evidence, and experiment outcomes."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Evidence(BaseModel):
    """A traceable scientific claim extracted from a source."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    paper_id: str
    claim: str
    section: str | None = None
    page: int | None = Field(default=None, ge=1)
    quote: str | None = None
    source_locator: str | None = None
    confidence: float = Field(ge=0, le=1)


class Paper(BaseModel):
    """Canonical representation of a scientific paper used by the system."""

    model_config = ConfigDict(extra="forbid")

    paper_id: str
    title: str
    abstract: str | None = None
    year: int | None = Field(default=None, ge=1900, le=2200)
    doi: str | None = None
    arxiv_id: str | None = None
    url: HttpUrl | None = None
    authors: list[str] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    tasks: list[str] = Field(default_factory=list)
    datasets: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    baselines: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    future_work: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExperimentResult(BaseModel):
    """Reproducible experiment result record."""

    model_config = ConfigDict(extra="forbid")

    experiment_id: str
    hypothesis_id: str
    code_revision: str
    dataset_manifest: str
    seed: int = Field(ge=0)
    metrics: dict[str, float]
    artifacts: list[str] = Field(default_factory=list)
    success: bool
    created_at: datetime = Field(default_factory=utcnow)
    notes: str | None = None
