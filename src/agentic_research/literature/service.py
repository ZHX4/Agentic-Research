"""Provider orchestration for Phase 1 literature retrieval."""

from __future__ import annotations

from collections import OrderedDict

from agentic_research.literature.identity import canonical_identity, deduplicate_papers
from agentic_research.retrieval.contracts import LiteratureRetriever, SearchHit, SearchQuery
from agentic_research.schemas import Paper


class LiteratureService:
    """Search configured providers and return canonicalized unique results.

    Provider relevance scores are provider-local and are therefore never
    compared across providers. The first configured provider supplies the
    representative hit for a canonical paper; duplicate paper records are
    merged before the representative hit is returned.
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
        representatives: OrderedDict[str, SearchHit] = OrderedDict()
        for hit in hits:
            identity = canonical_identity(hit.paper)
            if identity not in representatives:
                representatives[identity] = hit

        normalized: list[SearchHit] = []
        for paper in papers:
            identity = canonical_identity(paper)
            original = representatives.get(identity)
            if original is not None:
                normalized.append(original.model_copy(update={"paper": paper}))

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
