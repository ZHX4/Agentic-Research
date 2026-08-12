"""Hybrid scientific chunk retrieval for Phase 3."""

from __future__ import annotations

import sqlite3
from typing import Sequence

from agentic_research.retrieval.embeddings import EmbeddingProvider, cosine_similarity
from agentic_research.retrieval.reranking import Reranker
from agentic_research.schemas.phase3 import RetrievalFilters, RetrievalHit, RetrievalResponse
from agentic_research.world_model.store import ScientificWorldModel


class HybridRetriever:
    """Hybrid lexical/dense retriever with reciprocal-rank fusion."""

    def __init__(self, world: ScientificWorldModel, *, embedder: EmbeddingProvider | None = None, reranker: Reranker | None = None, rrf_k: int = 60) -> None:
        if rrf_k < 1:
            raise ValueError("rrf_k must be positive")
        self.world = world
        self.embedder = embedder
        self.reranker = reranker
        self.rrf_k = rrf_k

    def search(self, query: str, *, limit: int = 10, mode: str = "hybrid", filters: RetrievalFilters | None = None, candidate_limit: int | None = None) -> RetrievalResponse:
        if not query.strip():
            raise ValueError("query must not be empty")
        if limit < 1:
            raise ValueError("limit must be positive")
        if candidate_limit is not None and candidate_limit < limit:
            raise ValueError("candidate_limit must be greater than or equal to limit")
        if mode not in {"lexical", "dense", "hybrid"}:
            raise ValueError("mode must be lexical, dense, or hybrid")
        if mode in {"dense", "hybrid"} and self.embedder is None:
            raise RuntimeError("An embedding provider is required for dense or hybrid retrieval")

        filter_dict = (filters or RetrievalFilters()).model_dump()
        candidate_limit = candidate_limit or max(50, limit * 5)
        lexical_rows = self.world.lexical_search(query, limit=candidate_limit, filters=filter_dict) if mode in {"lexical", "hybrid"} else []
        dense_rows, dense_scores = self._dense_rows(query, candidate_limit, filter_dict) if mode in {"dense", "hybrid"} else ([], {})

        hits_by_id: dict[str, RetrievalHit] = {}
        lexical_rank = {row["chunk_id"]: rank for rank, row in enumerate(lexical_rows, start=1)}
        dense_rank = {row["chunk_id"]: rank for rank, row in enumerate(dense_rows, start=1)}
        lexical_score_by_id = {row["chunk_id"]: 1.0 / rank for rank, row in enumerate(lexical_rows, start=1)}
        row_by_id: dict[str, sqlite3.Row] = {row["chunk_id"]: row for row in [*lexical_rows, *dense_rows]}

        for chunk_id in sorted(set(lexical_rank) | set(dense_rank)):
            row = row_by_id[chunk_id]
            fused = 0.0
            reasons: list[str] = []
            if chunk_id in lexical_rank:
                fused += 1.0 / (self.rrf_k + lexical_rank[chunk_id])
                reasons.append("lexical")
            if chunk_id in dense_rank:
                fused += 1.0 / (self.rrf_k + dense_rank[chunk_id])
                reasons.append("dense")
            hits_by_id[chunk_id] = RetrievalHit(
                chunk_id=chunk_id,
                paper_id=row["paper_id"],
                title=row["title"],
                text=row["text"],
                section=row["section"],
                page_start=row["page_start"],
                page_end=row["page_end"],
                year=row["year"],
                source=row["source"],
                lexical_score=lexical_score_by_id.get(chunk_id, 0.0),
                dense_score=dense_scores.get(chunk_id),
                fused_score=fused,
                retrieval_reasons=reasons,
            )

        ranked = sorted(hits_by_id.values(), key=lambda hit: (-hit.fused_score, hit.chunk_id))[:candidate_limit]
        if self.reranker is not None and ranked:
            ranked = self.reranker.rerank(query, ranked)
        return RetrievalResponse(query=query, mode=mode, hits=ranked[:limit])

    def _dense_rows(self, query: str, limit: int, filters: dict[str, object]) -> tuple[list[sqlite3.Row], dict[str, float]]:
        if self.embedder is None:
            return [], {}
        query_vector = self.embedder.embed([query])[0]
        scored: list[tuple[float, sqlite3.Row]] = []
        for row in self.world.dense_candidates(embedding_model=self.embedder.model_id, filters=filters):
            score = self._cosine_from_blob(query_vector, row["vector"], int(row["vector_dim"]))
            scored.append((score, row))
        scored.sort(key=lambda pair: (-pair[0], pair[1]["chunk_id"]))
        selected = scored[:limit]
        return [row for _, row in selected], {row["chunk_id"]: score for score, row in selected}

    @staticmethod
    def _cosine_from_blob(query_vector: Sequence[float], blob: bytes, dimension: int) -> float:
        import struct
        if len(query_vector) != dimension:
            raise ValueError(f"Embedding dimension mismatch: query={len(query_vector)}, index={dimension}")
        expected_bytes = dimension * 4
        if len(blob) != expected_bytes:
            raise ValueError(f"Corrupt vector blob: expected {expected_bytes} bytes, got {len(blob)}")
        values = struct.unpack(f"<{dimension}f", blob)
        return cosine_similarity(query_vector, values)
