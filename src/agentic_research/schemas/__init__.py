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
from .phase3 import RetrievalFilters, RetrievalHit, RetrievalResponse, TraversalResult, WorldEdge, WorldNode
from .phase4 import GapDiscoveryConfig, GapDiscoveryResult, GapSignal
from .phase5 import (
    Counterevidence,
    DeepEvidenceCheck,
    GapVerificationResult,
    NoveltyVerificationConfig,
    NoveltyVerificationReport,
    PriorWorkMatch,
    SearchProbe,
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
    "RetrievalFilters",
    "RetrievalHit",
    "RetrievalResponse",
    "WorldNode",
    "WorldEdge",
    "TraversalResult",
    "GapDiscoveryConfig",
    "GapDiscoveryResult",
    "GapSignal",
    "SearchProbe",
    "PriorWorkMatch",
    "DeepEvidenceCheck",
    "Counterevidence",
    "NoveltyVerificationConfig",
    "GapVerificationResult",
    "NoveltyVerificationReport",
]
