"""Candidate research-gap models."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GapStatus(StrEnum):
    CANDIDATE = "candidate"
    SURVIVED = "survived"
    WEAKENED = "weakened"
    DISPROVED = "disproved"
    UNCERTAIN = "uncertain"


class GapCandidate(BaseModel):
    """Evidence-aware representation of a possible research gap.

    Phase 4 may only create candidates. Phase 5 is responsible for adversarial
    verification and any status transition away from ``candidate``.
    """

    model_config = ConfigDict(extra="forbid")

    gap_id: str = Field(min_length=1)
    gap_type: Literal[
        "missing_combination",
        "contradiction",
        "underexplored_condition",
        "unresolved_limitation",
        "cross_domain",
        "graph_negative_space",
    ]
    statement: str = Field(min_length=1)
    method: str | None = None
    task: str | None = None
    dataset: str | None = None
    evidence_paper_ids: list[str] = Field(default_factory=list)
    closest_prior_work_ids: list[str] = Field(default_factory=list)
    counterevidence_ids: list[str] = Field(default_factory=list)
    search_queries: list[str] = Field(default_factory=list)
    signal_ids: list[str] = Field(default_factory=list)
    support_count: int = Field(default=0, ge=0)
    coverage_ratio: float | None = Field(default=None, ge=0, le=1)
    structural_support: float = Field(default=0, ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    status: GapStatus = GapStatus.CANDIDATE
    rationale: str = Field(min_length=1)
