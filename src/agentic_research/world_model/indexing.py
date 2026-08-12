"""Index Phase 2 paper intelligence into the Phase 3 world model."""

from __future__ import annotations

from agentic_research.retrieval.embeddings import EmbeddingProvider
from agentic_research.schemas import Paper
from agentic_research.schemas.paper_intelligence import StructuredExtraction
from agentic_research.world_model.store import ScientificWorldModel


def index_extraction(
    world: ScientificWorldModel,
    paper: Paper,
    extraction: StructuredExtraction,
    *,
    embedder: EmbeddingProvider | None = None,
    batch_size: int = 64,
) -> None:
    """Persist a structured extraction and optional embeddings atomically."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    vectors: dict[str, list[float]] = {}
    if embedder is not None and extraction.chunks:
        for start in range(0, len(extraction.chunks), batch_size):
            batch = extraction.chunks[start:start + batch_size]
            encoded = embedder.embed([chunk.text for chunk in batch])
            if len(encoded) != len(batch):
                raise ValueError("Embedding provider returned a different number of vectors")
            for chunk, vector in zip(batch, encoded, strict=True):
                if len(vector) != embedder.dimension:
                    raise ValueError("Embedding provider returned an inconsistent dimension")
                vectors[chunk.chunk_id] = vector
    world.index_extraction(paper, extraction, vectors=vectors, vector_model=embedder.model_id if embedder else None)
