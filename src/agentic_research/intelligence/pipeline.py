"""End-to-end deterministic Phase 2 paper-intelligence pipeline."""

from __future__ import annotations

import hashlib
from pathlib import Path

from agentic_research.intelligence.citations import extract_citation_edges, extract_references
from agentic_research.intelligence.chunking import chunk_blocks
from agentic_research.intelligence.extraction import extract_claims, extract_fields
from agentic_research.intelligence.layout import extract_figures, extract_tables, iter_text_blocks
from agentic_research.intelligence.sections import detect_sections
from agentic_research.schemas import Paper
from agentic_research.schemas.paper_intelligence import StructuredExtraction

EXTRACTOR_VERSION = "phase2-native-1.0"


def extract_paper_intelligence(paper: Paper, pdf_path: Path) -> tuple[Paper, StructuredExtraction]:
    """Extract structure, chunks, tables, figures, claims, evidence, and citations from one PDF."""
    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)

    blocks = iter_text_blocks(pdf_path)
    sections = detect_sections(paper.paper_id, blocks)
    chunks = chunk_blocks(paper.paper_id, blocks, sections)
    tables = extract_tables(pdf_path, paper.paper_id)
    figures = extract_figures(pdf_path, paper.paper_id)

    reference_section = next(
        (
            section
            for section in reversed(sections)
            if section.normalized_title in {"references", "bibliography", "works cited"}
        ),
        None,
    )
    reference_blocks = [block for block in blocks if block.order >= reference_section.order] if reference_section else []
    references_text = "\n".join(block.text for block in reference_blocks)
    references = extract_references(paper, references_text) if references_text else []
    citation_edges = extract_citation_edges(paper, chunks, references)

    body_chunks = [chunk for chunk in chunks if not (reference_section and chunk.section_id == reference_section.section_id)]
    claims, evidence, links = extract_claims(paper.paper_id, body_chunks)
    fields = extract_fields(body_chunks, sections)
    enriched_paper = _merge_fields_and_evidence(paper, fields, evidence)

    extraction_id = hashlib.sha1(
        f"{paper.paper_id}|{pdf_path.resolve()}|{pdf_path.stat().st_size}|{pdf_path.stat().st_mtime_ns}".encode("utf-8")
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
        claims=claims,
        claim_links=links,
        extractor_version=EXTRACTOR_VERSION,
    )
    return enriched_paper, extraction


def _merge_fields_and_evidence(paper: Paper, fields: dict[str, list[str]], evidence) -> Paper:
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
            "field_values_are_candidates": True,
            "claim_evidence_is_extracted": True,
        },
    }
    return enriched
