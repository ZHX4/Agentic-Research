from agentic_research.literature.identity import (
    canonical_identity,
    deduplicate_papers,
    normalize_arxiv_id,
    normalize_doi,
)
from agentic_research.schemas import Paper


def test_normalize_doi() -> None:
    assert normalize_doi("https://doi.org/10.1234/ABC.") == "10.1234/abc"
    assert normalize_doi("doi:10.1234/ABC") == "10.1234/abc"


def test_normalize_arxiv_strips_revision() -> None:
    assert normalize_arxiv_id("https://arxiv.org/abs/2501.12345v3") == "2501.12345"
    assert normalize_arxiv_id("arXiv:2501.12345") == "2501.12345"


def test_dedup_merges_same_doi_across_sources() -> None:
    first = Paper(
        paper_id="W1",
        title="Example",
        year=2025,
        doi="https://doi.org/10.1234/ABC",
        authors=["Alice"],
    )
    second = Paper(
        paper_id="S1",
        title="Example",
        year=2025,
        doi="10.1234/abc",
        abstract="A longer abstract.",
        authors=["Alice", "Bob"],
    )
    papers = deduplicate_papers([first, second])
    assert len(papers) == 1
    assert papers[0].abstract == "A longer abstract."
    assert "Bob" in papers[0].authors
    assert canonical_identity(papers[0]) == "doi:10.1234/abc"
