"""Phase 3 schemas for retrieval and the scientific world model."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RetrievalFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year_from: int | None = Field(default=None, ge=1900, le=2200)
    year_to: int | None = Field(default=None, ge=1900, le=2200)
    temporal_cutoff: int | None = Field(default=None, ge=1900, le=2200)
    paper_ids: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_window(self) -> "RetrievalFilters":
        if self.year_from is not None and self.year_to is not None and self.year_from > self.year_to:
            raise ValueError("year_from must be <= year_to")
        if self.temporal_cutoff is not None:
            if self.year_from is not None and self.year_from > self.temporal_cutoff:
                raise ValueError("year_from cannot exceed temporal_cutoff")
            if self.year_to is not None and self.year_to > self.temporal_cutoff:
                raise ValueError("year_to cannot exceed temporal_cutoff")
        return self


class RetrievalHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(min_length=1)
    paper_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    text: str = Field(min_length=1)
    section: str | None = None
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    year: int | None = Field(default=None, ge=1900, le=2200)
    source: str | None = None
    lexical_score: float = Field(default=0, ge=0)
    dense_score: float | None = Field(default=None)
    fused_score: float = Field(default=0, ge=0)
    rerank_score: float | None = Field(default=None)
    retrieval_reasons: list[str] = Field(default_factory=list)


class RetrievalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    mode: Literal["lexical", "dense", "hybrid"]
    hits: list[RetrievalHit] = Field(default_factory=list)


class WorldNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(min_length=1)
    node_type: Literal[
        "paper", "section", "chunk", "claim", "evidence", "reference",
        "method", "dataset", "metric", "baseline", "task", "author",
    ]
    paper_id: str | None = None
    label: str = Field(min_length=1)
    payload: dict = Field(default_factory=dict)


class WorldEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    edge_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    edge_type: Literal[
        "contains", "supports", "qualifies", "contradicts", "contextualizes",
        "cites", "has_method", "has_dataset", "has_metric", "has_baseline",
        "has_task", "authored_by", "references",
    ]
    payload: dict = Field(default_factory=dict)


class TraversalResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_node_id: str = Field(min_length=1)
    depth: int = Field(ge=0)
    node_ids: list[str] = Field(default_factory=list)
    edge_ids: list[str] = Field(default_factory=list)
