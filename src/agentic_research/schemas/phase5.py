"""Phase 5 schemas for adversarial research-gap and novelty verification."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .gap import GapCandidate, GapStatus
from .paper import Paper


NoveltyVerdict = Literal["supported", "weakened", "disproved", "inconclusive"]
CoverageLevel = Literal["none", "limited", "moderate", "broad"]


class SearchProbe(BaseModel):
    """An auditable query used to challenge a candidate gap."""

    model_config = ConfigDict(extra="forbid")

    probe_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    source: str = Field(min_length=1)


class PriorWorkMatch(BaseModel):
    """A prior paper that is similar enough to challenge a candidate gap."""

    model_config = ConfigDict(extra="forbid")

    match_id: str = Field(min_length=1)
    paper: Paper
    source: str = Field(min_length=1)
    query: str = Field(min_length=1)
    similarity: float = Field(ge=0, le=1)
    method_overlap: float = Field(ge=0, le=1)
    dataset_overlap: float = Field(ge=0, le=1)
    task_overlap: float = Field(ge=0, le=1)
    title_overlap: float = Field(ge=0, le=1)
    exact_combination: bool
    challenge_type: Literal["direct", "near", "contextual"]
    rationale: str = Field(min_length=1)


class DeepEvidenceCheck(BaseModel):
    """Full-text evidence check for a high-priority prior-work candidate."""

    model_config = ConfigDict(extra="forbid")

    check_id: str = Field(min_length=1)
    paper_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    attempted: bool
    status: Literal["exact", "not_found", "unavailable", "failed"]
    media_type: Literal["application/pdf", "text/html", "unknown"]
    method_found: bool = False
    dataset_found: bool = False
    task_found: bool = False
    same_context_found: bool = False
    local_path: str | None = None
    sha256: str | None = None
    rationale: str = Field(min_length=1)


class Counterevidence(BaseModel):
    """Evidence discovered specifically to attack a candidate gap."""

    model_config = ConfigDict(extra="forbid")

    counterevidence_id: str = Field(min_length=1)
    paper_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    query: str = Field(min_length=1)
    claim: str = Field(min_length=1)
    severity: Literal["low", "medium", "high"]
    supports_gap: bool
    rationale: str = Field(min_length=1)


class NoveltyVerificationConfig(BaseModel):
    """Conservative controls for adversarial gap verification."""

    model_config = ConfigDict(extra="forbid")

    external_results_per_query: int = Field(default=10, ge=1, le=100)
    local_results_per_query: int = Field(default=10, ge=1, le=100)
    max_queries_per_gap: int = Field(default=12, ge=1, le=50)
    min_direct_similarity: float = Field(default=0.92, ge=0, le=1)
    near_match_similarity: float = Field(default=0.72, ge=0, le=1)
    min_broad_searches: int = Field(default=3, ge=1, le=50)
    temporal_cutoff: int | None = Field(default=None, ge=1900, le=2200)
    include_local: bool = True
    include_external: bool = True
    allow_status_transition: bool = True
    deep_verify: bool = True
    max_deep_verifications: int = Field(default=5, ge=0, le=25)
    require_deep_verification_for_supported: bool = True
    deep_verification_similarity_floor: float = Field(default=0.45, ge=0, le=1)

    @model_validator(mode="after")
    def validate_thresholds(self) -> "NoveltyVerificationConfig":
        if self.near_match_similarity > self.min_direct_similarity:
            raise ValueError("near_match_similarity must be <= min_direct_similarity")
        if not self.include_local and not self.include_external:
            raise ValueError("At least one search source must be enabled")
        if self.deep_verify and self.max_deep_verifications < 1:
            raise ValueError("max_deep_verifications must be positive when deep verification is enabled")
        return self


class GapVerificationResult(BaseModel):
    """Auditable Phase 5 verdict for one Phase 4 candidate."""

    model_config = ConfigDict(extra="forbid")

    verification_id: str = Field(min_length=1)
    gap_id: str = Field(min_length=1)
    original_status: GapStatus
    resulting_status: GapStatus
    verdict: NoveltyVerdict
    coverage: CoverageLevel
    confidence: float = Field(ge=0, le=1)
    query_probes: list[SearchProbe] = Field(default_factory=list)
    prior_work: list[PriorWorkMatch] = Field(default_factory=list)
    deep_evidence: list[DeepEvidenceCheck] = Field(default_factory=list)
    counterevidence: list[Counterevidence] = Field(default_factory=list)
    nearest_prior_work_ids: list[str] = Field(default_factory=list)
    searched_sources: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1)
    verified_candidate: GapCandidate


class NoveltyVerificationReport(BaseModel):
    """Batch Phase 5 report."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)
    temporal_cutoff: int | None = Field(default=None, ge=1900, le=2200)
    input_candidate_count: int = Field(ge=0)
    results: list[GapVerificationResult] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_integrity(self) -> "NoveltyVerificationReport":
        if self.input_candidate_count != len(self.results):
            raise ValueError("input_candidate_count must equal the number of verification results")
        ids = [result.verification_id for result in self.results]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate verification_id values are not allowed")
        gap_ids = [result.gap_id for result in self.results]
        if len(gap_ids) != len(set(gap_ids)):
            raise ValueError("Duplicate gap_id values are not allowed")
        for result in self.results:
            if result.gap_id != result.verified_candidate.gap_id:
                raise ValueError("gap_id must match verified_candidate.gap_id")
            if result.original_status != GapStatus.CANDIDATE:
                raise ValueError("Phase 5 input must be a Phase 4 candidate")
        return self
