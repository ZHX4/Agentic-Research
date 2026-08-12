from agentic_research.literature.service import LiteratureService
from agentic_research.retrieval.contracts import LiteratureRetriever, SearchHit, SearchQuery
from agentic_research.schemas import Paper


class StubRetriever(LiteratureRetriever):
    name = "stub"

    def __init__(self, papers: list[Paper]) -> None:
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
    with LiteratureService([StubRetriever([paper_a]), StubRetriever([paper_b])]) as service:
        hits = service.search(SearchQuery(text="same", limit=10))
    assert len(hits) == 1
    assert hits[0].paper.doi == "10.1/abc"
