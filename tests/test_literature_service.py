from agentic_research.literature.service import LiteratureService
from agentic_research.retrieval.contracts import LiteratureRetriever, SearchHit, SearchQuery
from agentic_research.schemas import Paper


class StubRetriever(LiteratureRetriever):
    def __init__(self, name: str, papers: list[Paper]) -> None:
        self.name = name
        self.papers = papers

    def search(self, query: SearchQuery) -> list[SearchHit]:
        return [
            SearchHit(paper=paper, score=0.5, source=self.name, retrieval_reason="stub")
            for paper in self.papers[: query.limit]
        ]


def test_service_deduplicates_across_sources() -> None:
    paper_a = Paper(paper_id="oa", title="Same Paper", year=2025, doi="10.1/ABC", abstract="A")
    paper_b = Paper(
        paper_id="s2",
        title="Same Paper",
        year=2025,
        doi="https://doi.org/10.1/abc",
        abstract="Longer",
    )
    with LiteratureService(
        [StubRetriever("openalex", [paper_a]), StubRetriever("s2", [paper_b])]
    ) as service:
        hits = service.search(SearchQuery(text="same", limit=10))
    assert len(hits) == 1
    assert hits[0].paper.doi == "10.1/abc"
    assert hits[0].paper.abstract == "Longer"
    assert hits[0].source == "openalex"


def test_service_does_not_compare_provider_scores() -> None:
    """Provider score order and canonical order disagree here on purpose.

    The provider returns the high-score paper first, but the canonical
    year-descending sort puts the newer low-score paper first. Only an
    implementation that ignores scores and applies the canonical sort passes.
    """
    old = Paper(paper_id="old", title="Old", year=2020, doi="10.1/old")
    new = Paper(paper_id="new", title="New", year=2025, doi="10.1/new")

    class ScoredRetriever(StubRetriever):
        def search(self, query: SearchQuery) -> list[SearchHit]:
            return [
                SearchHit(paper=old, score=0.9, source=self.name),
                SearchHit(paper=new, score=0.1, source=self.name),
            ]

    with LiteratureService([ScoredRetriever("provider", [old, new])]) as service:
        hits = service.search(SearchQuery(text="x", limit=10))
    assert [hit.paper.title for hit in hits] == ["New", "Old"]
