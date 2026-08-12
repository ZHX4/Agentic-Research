import httpx

from agentic_research.literature.sources.arxiv import ArxivAdapter
from agentic_research.literature.sources.openalex import OpenAlexAdapter
from agentic_research.literature.sources.semantic_scholar import SemanticScholarAdapter
from agentic_research.literature.transport import HttpClient, RateLimiter
from agentic_research.retrieval.contracts import SearchQuery


ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2501.12345v2</id>
    <title>  A Test Paper </title>
    <summary> An abstract for testing. </summary>
    <published>2025-01-10T00:00:00Z</published>
    <author><name>Alice Example</name></author>
    <link rel="alternate" href="https://arxiv.org/abs/2501.12345v2" />
    <link title="pdf" href="https://arxiv.org/pdf/2501.12345v2.pdf" />
    <arxiv:primary_category term="cs.LG" />
  </entry>
</feed>
"""


def _client(handler) -> HttpClient:
    return HttpClient(user_agent="test", rate_limiter=RateLimiter(0), transport=httpx.MockTransport(handler))


def test_openalex_adapter_maps_response_and_cutoff() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["api_key"] == "test-key"
        return httpx.Response(
            200,
            json={
                "meta": {"next_cursor": None},
                "results": [
                    {
                        "id": "https://openalex.org/W1",
                        "doi": "https://doi.org/10.1234/ABC",
                        "display_name": "A Test Paper",
                        "publication_year": 2024,
                        "abstract_inverted_index": {"An": [0], "abstract": [1]},
                        "authorships": [{"author": {"display_name": "Alice"}}],
                        "primary_location": {"landing_page_url": "https://example.org/paper"},
                        "relevance_score": 0.9,
                    },
                    {
                        "id": "https://openalex.org/W2",
                        "display_name": "Future Paper",
                        "publication_year": 2026,
                        "authorships": [],
                    },
                ],
            },
            request=request,
        )

    with _client(handler) as client:
        adapter = OpenAlexAdapter(api_key="test-key", client=client)
        hits = adapter.search(SearchQuery(text="test", limit=10, temporal_cutoff=2025))

    assert len(hits) == 1
    assert hits[0].paper.doi == "10.1234/abc"
    assert hits[0].paper.abstract == "An abstract"
    assert hits[0].paper.year == 2024


def test_temporal_cutoff_excludes_unknown_years() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"meta": {"next_cursor": None}, "results": [{"id": "https://openalex.org/W1", "display_name": "Unknown"}]},
            request=request,
        )

    with _client(handler) as client:
        adapter = OpenAlexAdapter(api_key="test-key", client=client)
        hits = adapter.search(SearchQuery(text="test", limit=10, temporal_cutoff=2025))
    assert hits == []


def test_semantic_scholar_adapter_maps_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["fields"]
        return httpx.Response(
            200,
            json={
                "total": 1,
                "data": [
                    {
                        "paperId": "S1",
                        "title": "A Test Paper",
                        "abstract": "Abstract",
                        "year": 2025,
                        "authors": [{"name": "Alice"}],
                        "externalIds": {"DOI": "10.1234/ABC", "ArXiv": "2501.12345v2"},
                        "url": "https://semanticscholar.org/paper/S1",
                        "openAccessPdf": {"url": "https://example.org/paper.pdf", "status": "GREEN"},
                        "citationCount": 3,
                    }
                ],
            },
            request=request,
        )

    with _client(handler) as client:
        adapter = SemanticScholarAdapter(client=client)
        hits = adapter.search(SearchQuery(text="test", limit=1, temporal_cutoff=2025))

    assert hits[0].paper.doi == "10.1234/abc"
    assert hits[0].paper.arxiv_id == "2501.12345"
    assert hits[0].paper.metadata["open_access_pdf_url"].endswith("paper.pdf")


def test_arxiv_adapter_parses_atom_without_double_encoding_query() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        query = request.url.params["search_query"]
        assert query == 'all:"machine learning"'
        return httpx.Response(200, text=ARXIV_XML, request=request, headers={"content-type": "application/atom+xml"})

    with _client(handler) as client:
        adapter = ArxivAdapter(client=client)
        hits = adapter.search(SearchQuery(text="machine learning", limit=1, temporal_cutoff=2025))

    assert hits[0].paper.arxiv_id == "2501.12345"
    assert hits[0].paper.title == "A Test Paper"
    assert hits[0].paper.year == 2025
    assert hits[0].paper.authors == ["Alice Example"]
