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
    """Extract structure, chunks, tables, figures, claims, and citations from one PDF."""
    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)

    blocks = iter_text_blocks(pdf_path)
    sections = detect_sections(paper.paper_id, blocks)
    chunks = chunk_blocks(paper.paper_id, blocks, sections)
    tables = extract_tables(pdf_path, paper.paper_id)
    figures = extract_figures(pdf_path, paper.paper_id)

    reference_section_ids = {
        section.section_id
        for section in sections
        if section.normalized_title in {"references", "bibliography", "works cited"}
    }
    reference_blocks = [block for block in blocks if (next((s.section_id for s in sections if s.page_start and s.page_start <= block.page <= (s.page_end or s.page_start)), None) in reference_section_ids)]
    references_text = "\n".join(block.text for block in reference_blocks)
    references = extract_references(paper, references_text) if references_text else []
    citation_edges = extract_citation_edges(paper, chunks, references)

    claims, links = extract_claims(
        paper.paper_id,
        [chunk for chunk in chunks if chunk.section_id not in reference_section_ids],
    )
    fields = extract_fields(chunks, sections)
    enriched_paper = _merge_fields_without_claiming_truth(paper, fields)

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


def _merge_fields_without_claiming_truth(paper: Paper, fields: dict[str, list[str]]) -> Paper:
    enriched = paper.model_copy(deep=True)
    for field, values in fields.items():
        existing = list(getattr(enriched, field))
        setattr(enriched, field, list(dict.fromkeys(existing + values)))
    enriched.metadata = {
        **enriched.metadata,
        "phase2_extraction": {
            "extractor_version": EXTRACTOR_VERSION,
            "field_values_are_candidates": True,
        },
    }
    return enriched
