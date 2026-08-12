from pathlib import Path

import fitz
import pytest
from pydantic import ValidationError

from agentic_research.intelligence.calibration import CalibrationExample, IsotonicCalibrator, calibration_report
from agentic_research.intelligence.citations import extract_citation_edges, extract_references
from agentic_research.intelligence.chunking import chunk_blocks
from agentic_research.intelligence.layout import TextBlock, extract_figures, extract_tables
from agentic_research.intelligence.sections import assign_section, detect_sections
from agentic_research.schemas import Evidence, Paper
from agentic_research.schemas.paper_intelligence import BoundingBox, ClaimEvidenceLink, StructuredExtraction, TextChunk


def _block(order: int, text: str, page: int = 1, size: float = 12, bold: bool = False) -> TextBlock:
    return TextBlock(
        block_id=f"b{order}",
        order=order,
        page=page,
        bbox=BoundingBox(x0=0, y0=order * 10, x1=500, y1=order * 10 + 10),
        text=text,
        font_size=size,
        bold=bold,
    )


def test_same_page_sections_use_document_order() -> None:
    blocks = [_block(0, "Introduction", size=16, bold=True), _block(1, "First paragraph."), _block(2, "Methods", size=16, bold=True), _block(3, "Second paragraph.")]
    sections = detect_sections("p1", blocks)
    assert len(sections) == 2
    first = assign_section(blocks[1], sections)
    second = assign_section(blocks[3], sections)
    assert first is not None and first.normalized_title == "introduction"
    assert second is not None and second.normalized_title == "methods"


def test_chunking_respects_section_boundaries() -> None:
    blocks = [_block(0, "Introduction", size=16, bold=True), _block(1, "This is an introduction sentence. Another sentence."), _block(2, "Methods", size=16, bold=True), _block(3, "We propose a method and evaluate it.")]
    sections = detect_sections("p1", blocks)
    chunks = chunk_blocks("p1", blocks, sections, target_chars=200, max_chars=500)
    assert chunks
    section_titles = [chunk.section_title for chunk in chunks]
    assert "introduction" in [title.lower() for title in section_titles if title]
    assert "methods" in [title.lower() for title in section_titles if title]


def test_reference_parsing_and_numeric_citation_edges() -> None:
    paper = Paper(paper_id="p1", title="Paper")
    refs_text = "[1] Alice. A reference title. 2024. doi:10.1234/ABC\n[2] Bob. Another title. 2023."
    refs = extract_references(paper, refs_text)
    assert refs[0].order == 1
    assert refs[0].doi == "10.1234/abc"
    chunk = TextChunk(chunk_id="c1", paper_id="p1", text="Prior work supports this result [1].")
    edges = extract_citation_edges(paper, [chunk], refs)
    assert len(edges) == 1
    assert edges[0].cited_paper_id == "doi:10.1234/abc"


def test_author_year_citation_edges() -> None:
    paper = Paper(paper_id="p1", title="Paper")
    refs_text = "[1] Smith, J. Retrieval Methods. 2024. doi:10.1234/SMITH"
    refs = extract_references(paper, refs_text)
    chunks = [
        TextChunk(chunk_id="c1", paper_id="p1", text="Prior work (Smith, 2024) supports this result."),
        TextChunk(chunk_id="c2", paper_id="p1", text="Smith et al. 2024 introduced the method."),
    ]
    edges = extract_citation_edges(paper, chunks, refs)
    assert len(edges) == 2
    assert all(edge.cited_paper_id == "doi:10.1234/smith" for edge in edges)


def test_confidence_calibrator_is_monotonic() -> None:
    examples = [CalibrationExample(raw_confidence=0.1, correct=False), CalibrationExample(raw_confidence=0.2, correct=True), CalibrationExample(raw_confidence=0.8, correct=True), CalibrationExample(raw_confidence=0.9, correct=True)]
    calibrator = IsotonicCalibrator.fit(examples)
    values = [calibrator.transform(x / 10) for x in range(11)]
    assert values == sorted(values)
    assert all(0 <= value <= 1 for value in values)


def test_calibration_report() -> None:
    examples = [CalibrationExample(raw_confidence=0.1, correct=False), CalibrationExample(raw_confidence=0.9, correct=True)]
    report = calibration_report(examples, bins=2)
    assert report.sample_count == 2
    assert 0 <= report.expected_calibration_error <= 1
    assert 0 <= report.brier_score <= 1


def test_structured_extraction_rejects_broken_evidence_link() -> None:
    with pytest.raises(ValidationError):
        StructuredExtraction(
            extraction_id="e1",
            paper_id="p1",
            evidence=[Evidence(evidence_id="ev1", paper_id="p1", claim="claim", confidence=0.5)],
            claim_links=[ClaimEvidenceLink(link_id="l1", claim_id="missing-claim", evidence_id="ev1", relation="supports", confidence=0.5)],
            extractor_version="test",
        )


def _make_table_pdf(path: Path) -> None:
    document = fitz.open()
    page = document.new_page(width=400, height=300)
    for x in (40, 180, 320):
        page.draw_line((x, 80), (x, 200), color=(0, 0, 0), width=1)
    for y in (80, 120, 160, 200):
        page.draw_line((40, y), (320, y), color=(0, 0, 0), width=1)
    page.insert_text((55, 105), "A")
    page.insert_text((195, 105), "B")
    page.insert_text((55, 145), "1")
    page.insert_text((195, 145), "2")
    document.save(path)
    document.close()


def test_table_extraction(tmp_path: Path) -> None:
    path = tmp_path / "table.pdf"
    _make_table_pdf(path)
    tables = extract_tables(path, "p1")
    assert tables
    assert tables[0].rows[0][0] == "A"
    assert tables[0].extraction_confidence > 0


def test_figure_extraction(tmp_path: Path) -> None:
    path = tmp_path / "figure.pdf"
    document = fitz.open()
    page = document.new_page(width=400, height=300)
    page.insert_text((50, 50), "Figure 1. Example image")
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
        "0000000c4944415408d763f8cfc0000000030001cdeb5a3e0000000049454e44ae426082"
    )
    page.insert_image(fitz.Rect(100, 80, 220, 180), stream=png)
    document.save(path)
    document.close()
    figures = extract_figures(path, "p1")
    assert figures
    assert figures[0].caption == "Figure 1. Example image"
