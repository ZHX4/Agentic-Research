from agentic_research.intelligence.citations import extract_citation_edges, extract_references
from agentic_research.schemas import Paper
from agentic_research.schemas.paper_intelligence import TextChunk


def test_author_year_citation_resolution() -> None:
    paper = Paper(paper_id="p1", title="Paper")
    refs = extract_references(
        paper,
        "Smith, Alice. Retrieval Methods. 2024. doi:10.1234/XYZ\nJones, Bob. Other Work. 2023.",
    )
    assert refs[0].authors == ["Smith"]
    chunk = TextChunk(chunk_id="c1", paper_id="p1", text="Prior work demonstrates this (Smith et al., 2024).")
    edges = extract_citation_edges(paper, [chunk], refs)
    assert len(edges) == 1
    assert edges[0].cited_reference_id == refs[0].reference_id
    assert edges[0].cited_paper_id == "doi:10.1234/xyz"
