from pathlib import Path

import pytest

from agentic_research.intelligence.chunking import chunk_blocks
from agentic_research.intelligence.sections import detect_sections
from agentic_research.retrieval.embeddings import HashEmbeddingProvider
from agentic_research.retrieval.hybrid import HybridRetriever
from agentic_research.retrieval.reranking import LexicalReranker
from agentic_research.schemas import Paper
from agentic_research.schemas.paper_intelligence import BoundingBox, StructuredExtraction, TextChunk
from agentic_research.schemas.phase3 import RetrievalFilters, WorldEdge, WorldNode
from agentic_research.world_model.indexing import index_extraction
from agentic_research.world_model.store import ScientificWorldModel
from tests.test_paper_intelligence import _block


def _paper(paper_id: str, title: str, year: int, source: str) -> Paper:
    return Paper(
        paper_id=paper_id,
        title=title,
        year=year,
        methods=["retrieval"],
        datasets=["dataset-a"],
        metrics=["accuracy"],
        tasks=["question answering"],
        metadata={"source": source},
    )


def _extraction(paper: Paper, texts: list[str]) -> StructuredExtraction:
    blocks = []
    for index, text in enumerate(texts):
        blocks.append(_block(index, text))
    sections = detect_sections(paper.paper_id, blocks)
    chunks = chunk_blocks(paper.paper_id, blocks, sections, target_chars=1000, max_chars=2000)
    return StructuredExtraction(
        extraction_id=f"e-{paper.paper_id}",
        paper_id=paper.paper_id,
        sections=sections,
        chunks=chunks,
        extractor_version="test",
    )


def test_world_model_index_and_lexical_retrieval(tmp_path: Path) -> None:
    db = tmp_path / "world.sqlite"
    paper = _paper("p1", "Retrieval study", 2024, "test")
    extraction = _extraction(paper, ["Retrieval improves factual accuracy.", "We evaluate question answering."])
    with ScientificWorldModel(db) as world:
        index_extraction(world, paper, extraction, embedder=HashEmbeddingProvider(32))
        response = HybridRetriever(world, embedder=HashEmbeddingProvider(32), reranker=LexicalReranker()).search(
            "factual accuracy", mode="hybrid", limit=5
        )
    assert response.hits
    assert response.hits[0].paper_id == "p1"
    assert "lexical" in response.hits[0].retrieval_reasons
    assert "dense" in response.hits[0].retrieval_reasons


def test_temporal_cutoff_excludes_future_documents(tmp_path: Path) -> None:
    db = tmp_path / "world.sqlite"
    old = _paper("old", "Old retrieval", 2020, "test")
    new = _paper("new", "New retrieval", 2026, "test")
    with ScientificWorldModel(db) as world:
        index_extraction(world, old, _extraction(old, ["retrieval evidence"]), embedder=HashEmbeddingProvider(32))
        index_extraction(world, new, _extraction(new, ["retrieval evidence"]), embedder=HashEmbeddingProvider(32))
        filters = RetrievalFilters(temporal_cutoff=2022)
        response = HybridRetriever(world, embedder=HashEmbeddingProvider(32)).search("retrieval", filters=filters, mode="hybrid", limit=10)
    assert response.hits
    assert all(hit.year is not None and hit.year <= 2022 for hit in response.hits)


def test_dense_requires_matching_dimension(tmp_path: Path) -> None:
    db = tmp_path / "world.sqlite"
    paper = _paper("p1", "Dense study", 2024, "test")
    with ScientificWorldModel(db) as world:
        index_extraction(world, paper, _extraction(paper, ["semantic retrieval"]), embedder=HashEmbeddingProvider(16))
        with pytest.raises(ValueError, match="dimension mismatch"):
            HybridRetriever(world, embedder=HashEmbeddingProvider(32)).search("semantic", mode="dense")


def test_graph_traversal_preserves_connected_nodes(tmp_path: Path) -> None:
    db = tmp_path / "world.sqlite"
    with ScientificWorldModel(db) as world:
        world.upsert_node(WorldNode(node_id="a", node_type="paper", paper_id="a", label="A"))
        world.upsert_node(WorldNode(node_id="b", node_type="paper", paper_id="b", label="B"))
        world.upsert_node(WorldNode(node_id="c", node_type="paper", paper_id="c", label="C"))
        world.upsert_edge(WorldEdge(edge_id="ab", source_id="a", target_id="b", edge_type="cites"))
        world.upsert_edge(WorldEdge(edge_id="bc", source_id="b", target_id="c", edge_type="cites"))
        world.commit()
        one = world.traverse("a", depth=1, edge_types={"cites"})
        two = world.traverse("a", depth=2, edge_types={"cites"})
    assert one.node_ids == ["a", "b"]
    assert two.node_ids == ["a", "b", "c"]
    assert two.edge_ids == ["ab", "bc"]


def test_world_model_rejects_unknown_traversal_start(tmp_path: Path) -> None:
    with ScientificWorldModel(tmp_path / "world.sqlite") as world:
        with pytest.raises(ValueError, match="Unknown start node"):
            world.traverse("missing")
