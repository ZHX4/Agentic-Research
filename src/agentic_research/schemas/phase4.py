"""Phase 4 schemas for deterministic research-gap discovery."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .gap import GapCandidate

GapSignalType = Literal[
    "missing_combination",
    "contradiction",
    "underexplored_condition",
    "unresolved_limitation",
    "cross_domain",
    "graph_negative_space",
]


class GapDiscoveryConfig(BaseModel):
    """Controls for deterministic Phase 4 discovery algorithms."""

    model_config = ConfigDict(extra="forbid")

    min_entity_support: int = Field(default=2, ge=1, le=1000)
    min_contradiction_support: int = Field(default=2, ge=2, le=1000)
    min_condition_support: int = Field(default=1, ge=1, le=1000)
    min_limitation_support: int = Field(default=2, ge=2, le=1000)
    min_graph_degree: int = Field(default=2, ge=1, le=1000)
    min_common_neighbors: int = Field(default=2, ge=1, le=1000)
    max_underexplored_coverage: float = Field(default=0.2, gt=0, le=1)
    max_candidates_per_type: int = Field(default=200, ge=1, le=10000)
    temporal_cutoff: int | None = Field(default=None, ge=1900, le=2200)
    include_types: set[GapSignalType] = Field(
        default_factory=lambda: {
            "missing_combination",
            "contradiction",
            "underexplored_condition",
            "unresolved_limitation",
            "cross_domain",
            "graph_negative_space",
        }
    )


class GapSignal(BaseModel):
    """A single auditable structural signal that produced a candidate gap."""

    model_config = ConfigDict(extra="forbid")

    signal_id: str = Field(min_length=1)
    gap_type: GapSignalType
    statement: str = Field(min_length=1)
    paper_ids: list[str] = Field(default_factory=list)
    node_ids: list[str] = Field(default_factory=list)
    support_count: int = Field(ge=0)
    structural_score: float = Field(ge=0, le=1)
    provenance: list[str] = Field(default_factory=list)


class GapDiscoveryResult(BaseModel):
    """Deterministic Phase 4 discovery output."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)
    temporal_cutoff: int | None = Field(default=None, ge=1900, le=2200)
    corpus_paper_count: int = Field(ge=0)
    signals: list[GapSignal] = Field(default_factory=list)
    candidates: list[GapCandidate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_signal_ids(self) -> "GapDiscoveryResult":
        ids = [signal.signal_id for signal in self.signals]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate signal_id values are not allowed")
        candidate_ids = [candidate.gap_id for candidate in self.candidates]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("Duplicate gap_id values are not allowed")
        signal_ids = set(ids)
        for candidate in self.candidates:
            if not set(candidate.signal_ids).issubset(signal_ids):
                raise ValueError(f"Candidate {candidate.gap_id} references an unknown signal")
            if candidate.status != "candidate":
                raise ValueError("Phase 4 may only emit candidate gap status")
        return self
