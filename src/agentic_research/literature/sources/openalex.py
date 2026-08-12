"""OpenAlex works search adapter."""

from __future__ import annotations

from typing import Any

import httpx

from agentic_research.literature.identity import normalize_doi
from agentic_research.literature.transport import HttpClient, RateLimiter
from agentic_research.retrieval.contracts import LiteratureRetriever, SearchHit, SearchQuery
from agentic_research.schemas import Paper

_BASE_URL = "https://api.openalex.org/works"


class OpenAlexAdapter(LiteratureRetriever):
    name = "openalex"

    def __init__(
        self,
        *,
        api_key: str,
        client: HttpClient | None = None,
        user_agent: str = "Agentic-Research/0.2 (+https://github.com/ZHX4/Agentic-Research)",
        timeout_seconds: float = 30.0,
        min_interval_seconds: float = 0.1,
    ) -> None:
        if not api_key.strip():
            raise ValueError("OpenAlex API key is required")
        self._api_key = api_key.strip()
        self._client = client or HttpClient(
            user_agent=user_agent,
            timeout_seconds=timeout_seconds,
            rate_limiter=RateLimiter(min_interval_seconds),
        )
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def search(self, query: SearchQuery) -> list[SearchHit]:
        results: list[SearchHit] = []
        cursor = "*"
        requested = query.limit

        while cursor and len(results) < requested:
            params: dict[str, object] = {
                "api_key": self._api_key,
                "search": query.text,
                "per_page": min(100, requested - len(results)),
                "cursor": cursor,
                "select": (
                    "id,doi,title,display_name,publication_year,publication_date,"
                    "authorships,primary_location,open_access,type,cited_by_count,relevance_score"
                ),
            }
            filters: list[str] = []
            if query.year_from is not None:
                filters.append(f"from_publication_date:{query.year_from}-01-01")
            if query.year_to is not None:
                filters.append(f"to_publication_date:{query.year_to}-12-31")
            if query.temporal_cutoff is not None:
                filters.append(f"to_publication_date:{query.temporal_cutoff}-12-31")
            if filters:
                params["filter"] = ",".join(filters)

            try:
                payload = self._client.get(_BASE_URL, params=params).json()
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                raise RuntimeError(f"OpenAlex request failed with HTTP {status}") from exc
            raw_results = payload.get("results", [])
            for raw in raw_results:
                paper = _paper_from_openalex(raw)
                if paper.year is not None and query.temporal_cutoff is not None and paper.year > query.temporal_cutoff:
                    continue
                results.append(
                    SearchHit(
                        paper=paper,
                        score=float(raw.get("relevance_score") or 0.0),
                        source=self.name,
                        retrieval_reason="OpenAlex relevance search",
                    )
                )
                if len(results) >= requested:
                    break
            cursor = payload.get("meta", {}).get("next_cursor")
            if not raw_results:
                break
        return results


def _paper_from_openalex(raw: dict[str, Any]) -> Paper:
    authors = [
        str(item.get("author", {}).get("display_name", "")).strip()
        for item in raw.get("authorships", [])
        if item.get("author", {}).get("display_name")
    ]
    primary_location = raw.get("primary_location") or {}
    landing_page = primary_location.get("landing_page_url")
    pdf_url = primary_location.get("pdf_url")
    source_id = raw.get("id")
    source_key = source_id.split("/")[-1] if isinstance(source_id, str) else str(source_id or "")
    metadata = {
        "source_ids": {"openalex": source_key},
        "open_access": raw.get("open_access") or {},
        "open_access_pdf_url": pdf_url,
        "type": raw.get("type"),
        "citation_count": raw.get("cited_by_count", 0),
    }
    return Paper(
        paper_id=source_key,
        title=str(raw.get("display_name") or raw.get("title") or "").strip(),
        year=raw.get("publication_year"),
        doi=normalize_doi(raw.get("doi")),
        url=landing_page,
        authors=authors,
        metadata=metadata,
    )
