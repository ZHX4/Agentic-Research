"""Canonical scientific domain schemas."""

from .gap import GapCandidate, GapStatus
from .hypothesis import ExperimentPlan, Hypothesis
from .paper import Evidence, ExperimentResult, Paper
from .paper_intelligence import (
    BoundingBox,
    CitationEdge,
    CitationReference,
    ClaimEvidenceLink,
    ExtractedClaim,
    FigureRecord,
    Section,
    StructuredExtraction,
    TableRecord,
    TextChunk,
)

__all__ = [
    "Paper",
    "Evidence",
    "ExperimentResult",
    "GapCandidate",
    "GapStatus",
    "Hypothesis",
    "ExperimentPlan",
    "BoundingBox",
    "Section",
    "TextChunk",
    "TableRecord",
    "FigureRecord",
    "CitationReference",
    "CitationEdge",
    "ClaimEvidenceLink",
    "ExtractedClaim",
    "StructuredExtraction",
]
