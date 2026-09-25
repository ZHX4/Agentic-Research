"""Provenance-join report: paper -> evidence -> gap -> verification -> hypothesis.

Measures inspectability at each phase boundary and explicitly reports
where the current Phase 6 source_gap_ids-only design loses direct
evidence linkage.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProvenanceJoinInput(BaseModel):
    """Counts supplied by the benchmark runner (no hidden state)."""

    model_config = ConfigDict(extra="forbid")

    gap_count: int = Field(ge=0)
    gaps_with_source_papers: int = Field(ge=0)
    gaps_with_passages: int = Field(ge=0)
    verdict_count: int = Field(ge=0)
    verdicts_with_evidence: int = Field(ge=0)
    hypothesis_count: int = Field(ge=0)
    hypotheses_with_gap_link: int = Field(ge=0)
    hypotheses_with_direct_paper_link: int = Field(ge=0)


class ProvenanceJoinReport(BaseModel):
    """Percentages plus explicit loss notes."""

    model_config = ConfigDict(extra="forbid")

    gaps_with_source_papers_pct: float = Field(ge=0, le=100)
    gaps_with_passages_pct: float = Field(ge=0, le=100)
    verdicts_with_evidence_pct: float = Field(ge=0, le=100)
    hypotheses_with_gap_link_pct: float = Field(ge=0, le=100)
    hypotheses_with_direct_paper_link_pct: float = Field(ge=0, le=100)
    known_loss: str = Field(min_length=1)
    notes: list[str] = Field(default_factory=list)


PHASE6_LOSS_NOTE = (
    "Phase 6 hypotheses retain source_gap_ids/source_statuses only "
    "(schemas/phase6.py); they carry no direct paper/passage IDs, so "
    "evidence linkage must join through the parent gap. Direct-link "
    "coverage below 100% is expected by design and reported, not hidden."
)


def _pct(have: int, total: int) -> float:
    return (100.0 * have / total) if total else 0.0


def build_provenance_report(counts: ProvenanceJoinInput) -> ProvenanceJoinReport:
    return ProvenanceJoinReport(
        gaps_with_source_papers_pct=_pct(counts.gaps_with_source_papers, counts.gap_count),
        gaps_with_passages_pct=_pct(counts.gaps_with_passages, counts.gap_count),
        verdicts_with_evidence_pct=_pct(counts.verdicts_with_evidence, counts.verdict_count),
        hypotheses_with_gap_link_pct=_pct(counts.hypotheses_with_gap_link, counts.hypothesis_count),
        hypotheses_with_direct_paper_link_pct=_pct(
            counts.hypotheses_with_direct_paper_link, counts.hypothesis_count
        ),
        known_loss=PHASE6_LOSS_NOTE,
        notes=[
            "paper -> evidence -> gap -> verification -> hypothesis join "
            "uses serialized IDs only; no hidden state."
        ],
    )
