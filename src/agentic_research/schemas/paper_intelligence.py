"""Canonical Phase 2 paper-intelligence models.

These models preserve document structure and provenance. They do not assert
scientific truth; extracted claims remain evidence candidates until evaluated.
"""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .paper import Evidence


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
    evidence_id: str = Field(min_length=1)
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
    evidence: list[Evidence] = Field(default_factory=list)
    claims: list[ExtractedClaim] = Field(default_factory=list)
    claim_links: list[ClaimEvidenceLink] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    extractor_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_referential_integrity(self) -> "StructuredExtraction":
        self._require_unique("section_id", self.sections)
        self._require_unique("chunk_id", self.chunks)
        self._require_unique("table_id", self.tables)
        self._require_unique("figure_id", self.figures)
        self._require_unique("reference_id", self.references)
        self._require_unique("edge_id", self.citation_edges)
        self._require_unique("evidence_id", self.evidence)
        self._require_unique("claim_id", self.claims)
        self._require_unique("link_id", self.claim_links)

        section_ids = {item.section_id for item in self.sections}
        chunk_ids = {item.chunk_id for item in self.chunks}
        reference_ids = {item.reference_id for item in self.references}
        evidence_ids = {item.evidence_id for item in self.evidence}
        claim_ids = {item.claim_id for item in self.claims}

        for section in self.sections:
            self._require_paper_id(section.paper_id)
            if section.parent_section_id is not None and section.parent_section_id not in section_ids:
                raise ValueError(f"Unknown parent_section_id: {section.parent_section_id}")
        for chunk in self.chunks:
            self._require_paper_id(chunk.paper_id)
            if chunk.section_id is not None and chunk.section_id not in section_ids:
                raise ValueError(f"Unknown chunk section_id: {chunk.section_id}")
        for record in [*self.tables, *self.figures, *self.references, *self.evidence, *self.claims]:
            self._require_paper_id(record.paper_id)
        for claim in self.claims:
            if claim.chunk_id not in chunk_ids:
                raise ValueError(f"Unknown claim chunk_id: {claim.chunk_id}")
            if claim.section_id is not None and claim.section_id not in section_ids:
                raise ValueError(f"Unknown claim section_id: {claim.section_id}")
        for edge in self.citation_edges:
            self._require_paper_id(edge.citing_paper_id)
            if edge.cited_reference_id not in reference_ids:
                raise ValueError(f"Unknown cited_reference_id: {edge.cited_reference_id}")
            if edge.citation_context_chunk_id is not None and edge.citation_context_chunk_id not in chunk_ids:
                raise ValueError(f"Unknown citation_context_chunk_id: {edge.citation_context_chunk_id}")
        for link in self.claim_links:
            if link.claim_id not in claim_ids:
                raise ValueError(f"Unknown claim_id: {link.claim_id}")
            if link.evidence_id not in evidence_ids:
                raise ValueError(f"Unknown evidence_id: {link.evidence_id}")
        return self

    def _require_paper_id(self, paper_id: str) -> None:
        if paper_id != self.paper_id:
            raise ValueError(f"Object belongs to paper_id={paper_id!r}, expected {self.paper_id!r}")

    @staticmethod
    def _require_unique(attribute: str, items: list[BaseModel]) -> None:
        values = [getattr(item, attribute) for item in items]
        if len(values) != len(set(values)):
            raise ValueError(f"Duplicate {attribute} values are not allowed")
