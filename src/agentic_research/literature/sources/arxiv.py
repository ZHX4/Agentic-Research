"""arXiv Atom API search adapter."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from xml.etree import ElementTree as ET

from agentic_research.literature.identity import normalize_arxiv_id
from agentic_research.literature.transport import HttpClient, RateLimiter
from agentic_research.retrieval.contracts import LiteratureRetriever, SearchHit, SearchQuery
from agentic_research.schemas import Paper

_BASE_URL = "https://export.arxiv.org/api/query"
_ATOM = "http://www.w3.org/2005/Atom"
_ARXIV = "http://arxiv.org/schemas/atom"


class ArxivAdapter(LiteratureRetriever):
    name = "arxiv"

    def __init__(
        self,
        *,
        client: HttpClient | None = None,
        user_agent: str = "Agentic-Research/0.2 (+https://github.com/ZHX4/Agentic-Research)",
        timeout_seconds: float = 30.0,
        min_interval_seconds: float = 3.0,
    ) -> None:
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
        start = 0
        escaped = query.text.replace('"', '\\"')
        while len(results) < query.limit:
            batch = min(100, query.limit - len(results))
            params = {
                "search_query": f'all:"{escaped}"',
                "start": start,
                "max_results": batch,
                "sortBy": "relevance",
                "sortOrder": "descending",
            }
            response = self._client.get(_BASE_URL, params=params)
            root = ET.fromstring(response.text)
            entries = root.findall(f"{{{_ATOM}}}entry")
            if not entries:
                break
            for entry in entries:
                paper = _paper_from_entry(entry)
                if paper.year is not None:
                    if query.year_from is not None and paper.year < query.year_from:
                        continue
                    if query.year_to is not None and paper.year > query.year_to:
                        continue
                    if query.temporal_cutoff is not None and paper.year > query.temporal_cutoff:
                        continue
                results.append(
                    SearchHit(
                        paper=paper,
                        score=0.0,
                        source=self.name,
                        retrieval_reason="arXiv relevance search",
                    )
                )
                if len(results) >= query.limit:
                    break
            start += len(entries)
            if len(entries) < batch:
                break
        return results


def _text(parent: ET.Element, tag: str) -> str | None:
    value = parent.findtext(f"{{{_ATOM}}}{tag}")
    return value.strip() if value else None


def _paper_from_entry(entry: ET.Element) -> Paper:
    entry_id = _text(entry, "id") or ""
    arxiv_id = normalize_arxiv_id(entry_id)
    title = _text(entry, "title") or ""
    abstract = _text(entry, "summary")
    published = _text(entry, "published")
    year = datetime.fromisoformat(published.replace("Z", "+00:00")).year if published else None
    authors = [
        name.text.strip()
        for author in entry.findall(f"{{{_ATOM}}}author")
        for name in [author.find(f"{{{_ATOM}}}name")]
        if name is not None and name.text
    ]
    links = entry.findall(f"{{{_ATOM}}}link")
    abs_url = next((link.get("href") for link in links if link.get("rel") == "alternate"), None)
    pdf_url = next((link.get("href") for link in links if link.get("title") == "pdf"), None)
    primary_category = entry.find(f"{{{_ARXIV}}}primary_category")
    metadata: dict[str, Any] = {
        "source_ids": {"arxiv": arxiv_id or ""},
        "open_access_pdf_url": pdf_url,
        "primary_category": primary_category.get("term") if primary_category is not None else None,
    }
    return Paper(
        paper_id=arxiv_id or entry_id,
        title=" ".join(title.split()),
        abstract=" ".join(abstract.split()) if abstract else None,
        year=year,
        arxiv_id=arxiv_id,
        url=abs_url,
        authors=authors,
        metadata=metadata,
    )
