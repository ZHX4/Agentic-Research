"""End-to-end deterministic Phase 2 paper-intelligence pipeline."""

from __future__ import annotations

import hashlib
from pathlib import Path

from agentic_research.intelligence.calibration import IsotonicCalibrator
from agentic_research.intelligence.citations import extract_citation_edges, extract_references
from agentic_research.intelligence.chunking import chunk_blocks
from agentic_research.intelligence.extraction import extract_claims, extract_fields
from agentic_research.intelligence.layout import extract_figures, extract_tables, iter_text_blocks
from agentic_research.intelligence.sections import detect_sections
from agentic_research.schemas import Evidence, Paper
from agentic_research.schemas.paper_intelligence import Section, StructuredExtraction

EXTRACTOR_VERSION = "phase2-native-1.2"
_REFERENCE_TITLES = {"references", "bibliography", "works cited"}


def _sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while data := handle.read(chunk_size):
            digest.update(data)
    return digest.hexdigest()


def _reference_range(sections: list[Section]) -> tuple[int, int | None] | None:
    """Return document-order bounds for the reference section and its descendants."""
    candidates = [section for section in sections if section.normalized_title in _REFERENCE_TITLES]
    if not candidates:
        return None
    reference = candidates[-1]
    next_boundary: int | None = None
    for section in sections:
        if section.order <= reference.order:
            continue
        if section.level <= reference.level:
            next_boundary = section.order
            break
    return reference.order, next_boundary


def extract_paper_intelligence(
    paper: Paper,
    pdf_path: Path,
    *,
    calibrator: IsotonicCalibrator | None = None,
) -> tuple[Paper, StructuredExtraction]:
    """Extract structure, evidence, claims, and citations from one PDF."""
    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)

    document_digest = _sha256_file(pdf_path)
    blocks = iter_text_blocks(pdf_path)
    sections = detect_sections(paper.paper_id, blocks)
    chunks = chunk_blocks(paper.paper_id, blocks, sections)
    tables = extract_tables(pdf_path, paper.paper_id)
    figures = extract_figures(pdf_path, paper.paper_id)

    reference_range = _reference_range(sections)
    reference_section = None
    if reference_range is not None:
        reference_start, reference_end = reference_range
        reference_section = next(section for section in sections if section.order == reference_start)
        reference_blocks = [
            block
            for block in blocks
            if block.order >= reference_start and (reference_end is None or block.order < reference_end)
        ]
    else:
        reference_blocks = []

    references_text = "\n".join(block.text for block in reference_blocks)
    references = extract_references(paper, references_text) if references_text else []

    reference_section_ids = {
        section.section_id
        for section in sections
        if reference_range is not None
        and section.order >= reference_range[0]
        and (reference_range[1] is None or section.order < reference_range[1])
    }
    body_chunks = [chunk for chunk in chunks if chunk.section_id not in reference_section_ids]
    citation_edges = extract_citation_edges(paper, body_chunks, references)
    claims, evidence, links = extract_claims(paper.paper_id, body_chunks)

    if len(claims) != len(evidence) or len(claims) != len(links):
        raise RuntimeError("Claim, evidence, and provenance-link counts must remain aligned")

    calibration_applied = calibrator is not None
    if calibrator is not None:
        for claim, item in zip(claims, evidence, strict=True):
            calibrated = calibrator.transform(claim.raw_confidence)
            claim.calibrated_confidence = calibrated
            item.confidence = calibrated

    fields = extract_fields(body_chunks, sections)
    enriched_paper = _merge_fields_and_evidence(
        paper,
        fields,
        evidence,
        document_digest,
        calibration_applied,
    )

    extraction_id = hashlib.sha1(
        f"{paper.paper_id}|{document_digest}|{EXTRACTOR_VERSION}".encode("utf-8")
    ).hexdigest()[:20]
    extraction = StructuredExtraction(
        extraction_id=f"extract-{extraction_id}",
        paper_id=paper.paper_id,
        sections=sections,
        chunks=chunks,
        tables=tables,
        figures=figures,
        references=references,
        citation_edges=citation_edges,
        evidence=evidence,
        claims=claims,
        claim_links=links,
        extractor_version=EXTRACTOR_VERSION,
    )
    return enriched_paper, extraction


def _merge_fields_and_evidence(
    paper: Paper,
    fields: dict[str, list[str]],
    evidence: list[Evidence],
    document_digest: str,
    calibration_applied: bool,
) -> Paper:
    enriched = paper.model_copy(deep=True)
    for field, values in fields.items():
        existing = list(getattr(enriched, field))
        setattr(enriched, field, list(dict.fromkeys(existing + values)))
    existing_evidence = {item.evidence_id: item for item in enriched.evidence}
    existing_evidence.update({item.evidence_id: item for item in evidence})
    enriched.evidence = list(existing_evidence.values())
    enriched.metadata = {
        **enriched.metadata,
        "phase2_extraction": {
            "extractor_version": EXTRACTOR_VERSION,
            "document_sha256": document_digest,
            "field_values_are_candidates": True,
            "claim_evidence_is_extracted": True,
            "calibration_applied": calibration_applied,
        },
    }
    return enriched
