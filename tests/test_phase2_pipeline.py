from pathlib import Path

import fitz

from agentic_research.intelligence.pipeline import extract_paper_intelligence
from agentic_research.schemas import Paper


def _make_paper_pdf(path: Path) -> None:
    document = fitz.open()
    page = document.new_page(width=600, height=800)
    page.insert_text((60, 60), "A Study on Retrieval", fontsize=18)
    page.insert_text((60, 100), "Introduction", fontsize=16)
    page.insert_text((60, 130), "Retrieval systems can improve factual accuracy [1].")
    page.insert_text((60, 160), "Methods", fontsize=16)
    page.insert_text((60, 190), "We propose a retrieval method and evaluate it.")
    page.insert_text((60, 220), "Results", fontsize=16)
    page.insert_text((60, 250), "Our method improves accuracy over the baseline.")
    page.insert_text((60, 280), "References", fontsize=16)
    page.insert_text((60, 310), "[1] Alice Example. Retrieval Systems. 2024. doi:10.1234/XYZ")
    document.save(path)
    document.close()


def test_end_to_end_pipeline(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    _make_paper_pdf(pdf)
    paper = Paper(paper_id="p1", title="A Study on Retrieval", year=2025)
    enriched, extraction = extract_paper_intelligence(paper, pdf)

    assert extraction.paper_id == "p1"
    assert len(extraction.sections) >= 4
    assert extraction.chunks
    assert extraction.references
    assert extraction.references[0].doi == "10.1234/xyz"
    assert extraction.citation_edges
    assert extraction.claims
    assert extraction.claim_links
    assert enriched.metadata["phase2_extraction"]["field_values_are_candidates"] is True
    assert all(claim.section_id != extraction.sections[-1].section_id for claim in extraction.claims)
