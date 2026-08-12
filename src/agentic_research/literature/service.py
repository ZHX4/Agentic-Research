"""Provider orchestration for Phase 1 literature retrieval."""

from __future__ import annotations

from contextlib import ExitStack

from agentic_research.literature.identity import deduplicate_papers
from agentic_research.retrieval.contracts import LiteratureRetriever, SearchHit, SearchQuery
from agentic_research.schemas import Paper


class LiteratureService:
    """Search one or more providers and normalize the result set.

    This service deliberately performs no semantic reranking. That belongs to
    the retrieval/world-model phases. Phase 1 is responsible for trustworthy
    source access, normalization, temporal filtering, and deduplication.
    """

    def __init__(self, retrievers: list[LiteratureRetriever]) -> None:
        if not retrievers:
            raise ValueError("At least one retriever is required")
        self._retrievers = retrievers

    def search(self, query: SearchQuery) -> list[SearchHit]:
        hits: list[SearchHit] = []
        for retriever in self._retrievers:
            hits.extend(retriever.search(query))
        papers = deduplicate_papers(hit.paper for hit in hits)
        hit_by_identity = {
            _identity_key(hit.paper): hit
            for hit in hits
        }
        normalized: list[SearchHit] = []
        for paper in papers:
            original = hit_by_identity.get(_identity_key(paper))
            if original is not None:
                normalized.append(original.model_copy(update={"paper": paper}))
        normalized.sort(key=lambda hit: (-hit.score, hit.paper.title.lower()))
        return normalized[: query.limit]

    def close(self) -> None:
        for retriever in self._retrievers:
            close = getattr(retriever, "close", None)
            if callable(close):
                close()

    def __enter__(self) -> "LiteratureService":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _identity_key(paper: Paper) -> str:
    metadata = paper.metadata.get("source_ids", {})
    if paper.doi:
        return f"doi:{paper.doi.lower()}"
    if paper.arxiv_id:
        return f"arxiv:{paper.arxiv_id.lower()}"
    if isinstance(metadata, dict):
        for source, value in metadata.items():
            if value:
                return f"{source}:{value}"
    return f"title:{paper.title.lower()}|year:{paper.year}"
