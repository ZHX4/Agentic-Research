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
    paper_b = Paper(paper_id="s2", title="Same Paper", year=2025, doi="https://doi.org/10.1/abc", abstract="Longer")
    with LiteratureService([StubRetriever("openalex", [paper_a]), StubRetriever("s2", [paper_b])]) as service:
        hits = service.search(SearchQuery(text="same", limit=10))
    assert len(hits) == 1
    assert hits[0].paper.doi == "10.1/abc"
    assert hits[0].paper.abstract == "Longer"
    assert hits[0].source == "openalex"


def test_service_does_not_compare_provider_scores() -> None:
    first = Paper(paper_id="a", title="First", year=2025, doi="10.1/first")
    second = Paper(paper_id="b", title="Second", year=2025, doi="10.1/second")

    class ScoredRetriever(StubRetriever):
        def search(self, query: SearchQuery) -> list[SearchHit]:
            return [
                SearchHit(paper=first, score=0.1, source=self.name),
                SearchHit(paper=second, score=0.9, source=self.name),
            ]

    with LiteratureService([ScoredRetriever("provider", [first, second])]) as service:
        hits = service.search(SearchQuery(text="x", limit=10))
    assert [hit.paper.title for hit in hits] == ["First", "Second"]
