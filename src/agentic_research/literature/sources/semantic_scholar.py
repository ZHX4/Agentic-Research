"""Semantic Scholar Academic Graph search adapter."""

from __future__ import annotations

from typing import Any

from agentic_research.literature.identity import normalize_arxiv_id, normalize_doi
from agentic_research.literature.transport import HttpClient, RateLimiter
from agentic_research.retrieval.contracts import LiteratureRetriever, SearchHit, SearchQuery
from agentic_research.schemas import Paper

_BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
_FIELDS = (
    "paperId,title,abstract,year,authors,externalIds,url,openAccessPdf,"
    "publicationDate,journal,venue,citationCount"
)


class SemanticScholarAdapter(LiteratureRetriever):
    name = "semantic_scholar"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        client: HttpClient | None = None,
        min_interval_seconds: float = 1.0,
    ) -> None:
        headers = {"x-api-key": api_key} if api_key else {}
        self._client = client or HttpClient(
            user_agent="Agentic-Research/0.2 (+https://github.com/ZHX4/Agentic-Research)",
            rate_limiter=RateLimiter(min_interval_seconds),
        )
        # A custom HttpClient is already fully constructed, so API-key headers
        # are intentionally handled by the default client only in this adapter.
        # When an injected client is used for tests, its transport can assert the
        # request independently.
        if headers and client is None:
            # Recreate the client with the authenticated header through a tiny
            # dedicated transport wrapper is unnecessarily complex; use the
            # public query parameter only when available is not supported.
            self._client.close()
            self._client = HttpClientWithHeaders(
                headers=headers,
                rate_limiter=RateLimiter(min_interval_seconds),
            )
            self._owns_client = True
        else:
            self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def search(self, query: SearchQuery) -> list[SearchHit]:
        results: list[SearchHit] = []
        offset = 0
        page_size = min(100, query.limit)

        while len(results) < query.limit:
            params: dict[str, object] = {
                "query": query.text,
                "limit": min(page_size, query.limit - len(results)),
                "offset": offset,
                "fields": _FIELDS,
            }
            if query.year_from is not None or query.year_to is not None:
                low = query.year_from or 1900
                high = query.year_to or 2200
                if query.temporal_cutoff is not None:
                    high = min(high, query.temporal_cutoff)
                params["year"] = f"{low}-{high}"
            elif query.temporal_cutoff is not None:
                params["year"] = f"1900-{query.temporal_cutoff}"

            payload = self._client.get(_BASE_URL, params=params).json()
            data = payload.get("data", [])
            if not data:
                break
            for raw in data:
                paper = _paper_from_semantic_scholar(raw)
                if paper.year is not None and query.temporal_cutoff and paper.year > query.temporal_cutoff:
                    continue
                results.append(
                    SearchHit(
                        paper=paper,
                        score=0.0,
                        source=self.name,
                        retrieval_reason="Semantic Scholar relevance search",
                    )
                )
                if len(results) >= query.limit:
                    break
            offset += len(data)
            if offset >= int(payload.get("total", offset)):
                break
        return results


def _paper_from_semantic_scholar(raw: dict[str, Any]) -> Paper:
    external_ids = raw.get("externalIds") or {}
    doi = normalize_doi(external_ids.get("DOI"))
    arxiv_id = normalize_arxiv_id(external_ids.get("ArXiv"))
    paper_id = str(raw.get("paperId") or "")
    authors = [str(a.get("name", "")).strip() for a in raw.get("authors", []) if a.get("name")]
    oa_pdf = raw.get("openAccessPdf") or {}
    metadata = {
        "source_ids": {"semantic_scholar": paper_id},
        "open_access_pdf_url": oa_pdf.get("url"),
        "open_access_status": oa_pdf.get("status"),
        "venue": raw.get("venue"),
        "journal": raw.get("journal"),
        "citation_count": raw.get("citationCount", 0),
    }
    return Paper(
        paper_id=paper_id,
        title=str(raw.get("title") or "").strip(),
        abstract=raw.get("abstract"),
        year=raw.get("year"),
        doi=doi,
        arxiv_id=arxiv_id,
        url=raw.get("url"),
        authors=authors,
        metadata=metadata,
    )


class HttpClientWithHeaders(HttpClient):
    """Authenticated HttpClient used only by Semantic Scholar."""

    def __init__(self, *, headers: dict[str, str], rate_limiter: RateLimiter) -> None:
        import httpx

        super().__init__(user_agent="Agentic-Research/0.2 (+https://github.com/ZHX4/Agentic-Research)", rate_limiter=rate_limiter)
        self._client.headers.update(headers)
