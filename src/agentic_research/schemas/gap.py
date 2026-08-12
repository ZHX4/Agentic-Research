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
    """Evidence-aware representation of a possible research gap."""

    model_config = ConfigDict(extra="forbid")

    gap_id: str
    gap_type: Literal[
        "missing_combination",
        "contradiction",
        "underexplored_condition",
        "unresolved_limitation",
        "cross_domain",
    ]
    statement: str
    method: str | None = None
    task: str | None = None
    dataset: str | None = None
    evidence_paper_ids: list[str] = Field(default_factory=list)
    closest_prior_work_ids: list[str] = Field(default_factory=list)
    counterevidence_ids: list[str] = Field(default_factory=list)
    search_queries: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    status: GapStatus = GapStatus.CANDIDATE
    rationale: str
