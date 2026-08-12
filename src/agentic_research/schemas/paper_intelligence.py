"""Canonical Phase 2 paper-intelligence models.

These models preserve document structure and provenance. They do not assert
scientific truth; extracted claims remain evidence candidates until evaluated.
"""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BoundingBox(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x0: float
    y0: float
    x1: float
    y1: float


class Section(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section_id: str = Field(min_length=1)
    paper_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    normalized_title: str = Field(min_length=1)
    level: int = Field(ge=1)
    order: int = Field(ge=0)
    parent_section_id: str | None = None
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)


class TextChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(min_length=1)
    paper_id: str = Field(min_length=1)
    section_id: str | None = None
    section_title: str | None = None
    text: str = Field(min_length=1)
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)
    block_ids: list[str] = Field(default_factory=list)


class TableRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    table_id: str = Field(min_length=1)
    paper_id: str = Field(min_length=1)
    page: int = Field(ge=1)
    bbox: BoundingBox
    rows: list[list[str]]
    markdown: str = ""
    caption: str | None = None
    extraction_confidence: float = Field(ge=0, le=1)


class FigureRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    figure_id: str = Field(min_length=1)
    paper_id: str = Field(min_length=1)
    page: int = Field(ge=1)
    bbox: BoundingBox
    image_digest: str | None = None
    image_xref: int | None = None
    caption: str | None = None
    extraction_confidence: float = Field(ge=0, le=1)


class CitationReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_id: str = Field(min_length=1)
    paper_id: str = Field(min_length=1)
    order: int | None = Field(default=None, ge=1)
    raw_text: str = Field(min_length=1)
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    year: int | None = Field(default=None, ge=1800, le=2200)
    doi: str | None = None
    arxiv_id: str | None = None
    url: str | None = None
    extraction_confidence: float = Field(ge=0, le=1)


class CitationEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    edge_id: str = Field(min_length=1)
    citing_paper_id: str = Field(min_length=1)
    cited_reference_id: str = Field(min_length=1)
    cited_paper_id: str | None = None
    citation_context_chunk_id: str | None = None
    marker: str | None = None
    confidence: float = Field(ge=0, le=1)


class ClaimEvidenceLink(BaseModel):
    model_config = ConfigDict(extra="forbid")

    link_id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    evidence_chunk_id: str = Field(min_length=1)
    relation: Literal["supports", "qualifies", "contradicts", "contextualizes"]
    confidence: float = Field(ge=0, le=1)


class ExtractedClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(min_length=1)
    paper_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    section_id: str | None = None
    chunk_id: str = Field(min_length=1)
    page: int | None = Field(default=None, ge=1)
    claim_type: Literal[
        "result",
        "method",
        "limitation",
        "dataset",
        "evaluation",
        "general",
    ]
    raw_confidence: float = Field(ge=0, le=1)
    calibrated_confidence: float | None = Field(default=None, ge=0, le=1)


class StructuredExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extraction_id: str = Field(min_length=1)
    paper_id: str = Field(min_length=1)
    sections: list[Section] = Field(default_factory=list)
    chunks: list[TextChunk] = Field(default_factory=list)
    tables: list[TableRecord] = Field(default_factory=list)
    figures: list[FigureRecord] = Field(default_factory=list)
    references: list[CitationReference] = Field(default_factory=list)
    citation_edges: list[CitationEdge] = Field(default_factory=list)
    claims: list[ExtractedClaim] = Field(default_factory=list)
    claim_links: list[ClaimEvidenceLink] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    extractor_version: str = Field(min_length=1)
