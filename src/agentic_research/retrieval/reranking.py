"""Reranking providers for Phase 3 retrieval."""

from __future__ import annotations

from abc import ABC, abstractmethod
import re
from typing import Sequence

from agentic_research.schemas.phase3 import RetrievalHit

_TOKEN = re.compile(r"[A-Za-z0-9_]+")


class Reranker(ABC):
    name: str

    @abstractmethod
    def rerank(self, query: str, hits: Sequence[RetrievalHit]) -> list[RetrievalHit]:
        raise NotImplementedError


class LexicalReranker(Reranker):
    """Deterministic lexical-overlap reranker used as a safe default."""

    name = "lexical-overlap"

    def rerank(self, query: str, hits: Sequence[RetrievalHit]) -> list[RetrievalHit]:
        query_tokens = set(_TOKEN.findall(query.lower()))
        output: list[RetrievalHit] = []
        for hit in hits:
            tokens = set(_TOKEN.findall(hit.text.lower()))
            overlap = len(query_tokens & tokens) / max(1, len(query_tokens))
            score = 0.75 * overlap + 0.25 * hit.fused_score
            output.append(hit.model_copy(update={"rerank_score": score}))
        return sorted(output, key=lambda item: (-float(item.rerank_score or 0), item.chunk_id))


class CrossEncoderReranker(Reranker):
    """Optional cross-encoder reranker backed by sentence-transformers."""

    name = "cross-encoder"

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is required for this reranker; install the embeddings extra"
            ) from exc
        self._model = CrossEncoder(model_name)
        self.model_name = model_name

    def rerank(self, query: str, hits: Sequence[RetrievalHit]) -> list[RetrievalHit]:
        if not hits:
            return []
        scores = self._model.predict([(query, hit.text) for hit in hits])
        output = [hit.model_copy(update={"rerank_score": float(score)}) for hit, score in zip(hits, scores, strict=True)]
        return sorted(output, key=lambda item: (-float(item.rerank_score or 0), item.chunk_id))
