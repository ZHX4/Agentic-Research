from pathlib import Path
import sqlite3
import struct
import hashlib

import pytest

from agentic_research.intelligence.chunking import chunk_blocks
from agentic_research.intelligence.sections import detect_sections
from agentic_research.retrieval.embeddings import HashEmbeddingProvider
from agentic_research.retrieval.hybrid import HybridRetriever
from agentic_research.retrieval.reranking import LexicalReranker
from agentic_research.schemas import Paper
from agentic_research.schemas.paper_intelligence import StructuredExtraction
from agentic_research.schemas.phase3 import RetrievalFilters, WorldEdge, WorldNode
from agentic_research.world_model.indexing import index_extraction
from agentic_research.world_model.store import ScientificWorldModel
from tests.test_paper_intelligence import _block


def _paper(paper_id: str, title: str, year: int, source: str) -> Paper:
    return Paper(
        paper_id=paper_id,
        title=title,
        year=year,
        authors=["Alice Researcher"],
        methods=["retrieval"],
        datasets=["dataset-a"],
        metrics=["accuracy"],
        tasks=["question answering"],
        metadata={"source": source},
    )


def _extraction(paper: Paper, texts: list[str]) -> StructuredExtraction:
    blocks = [_block(index, text) for index, text in enumerate(texts)]
    sections = detect_sections(paper.paper_id, blocks)
    chunks = chunk_blocks(paper.paper_id, blocks, sections, target_chars=1000, max_chars=2000)
    return StructuredExtraction(extraction_id=f"e-{paper.paper_id}", paper_id=paper.paper_id, sections=sections, chunks=chunks, extractor_version="test")


def test_world_model_index_and_hybrid_retrieval(tmp_path: Path) -> None:
    db = tmp_path / "world.sqlite"
    paper = _paper("p1", "Retrieval study", 2024, "test")
    extraction = _extraction(paper, ["Retrieval improves factual accuracy.", "We evaluate question answering."])
    embedder = HashEmbeddingProvider(32)
    with ScientificWorldModel(db) as world:
        index_extraction(world, paper, extraction, embedder=embedder)
        response = HybridRetriever(world, embedder=embedder, reranker=LexicalReranker()).search("factual accuracy", mode="hybrid", limit=5)
    assert response.hits
    assert response.hits[0].paper_id == "p1"
    assert "lexical" in response.hits[0].retrieval_reasons
    assert "dense" in response.hits[0].retrieval_reasons
    assert response.hits[0].rerank_score is not None


def test_temporal_cutoff_excludes_future_documents(tmp_path: Path) -> None:
    db = tmp_path / "world.sqlite"
    old = _paper("old", "Old retrieval", 2020, "test")
    new = _paper("new", "New retrieval", 2026, "test")
    embedder = HashEmbeddingProvider(32)
    with ScientificWorldModel(db) as world:
        index_extraction(world, old, _extraction(old, ["retrieval evidence"]), embedder=embedder)
        index_extraction(world, new, _extraction(new, ["retrieval evidence"]), embedder=embedder)
        response = HybridRetriever(world, embedder=embedder).search("retrieval", filters=RetrievalFilters(temporal_cutoff=2022), mode="hybrid", limit=10)
    assert response.hits
    assert all(hit.year is not None and hit.year <= 2022 for hit in response.hits)


def test_metadata_filters_apply_to_lexical_and_dense(tmp_path: Path) -> None:
    db = tmp_path / "world.sqlite"
    a = _paper("a", "Retrieval A", 2020, "source-a")
    b = _paper("b", "Retrieval B", 2021, "source-b")
    embedder = HashEmbeddingProvider(32)
    with ScientificWorldModel(db) as world:
        index_extraction(world, a, _extraction(a, ["retrieval evidence A"]), embedder=embedder)
        index_extraction(world, b, _extraction(b, ["retrieval evidence B"]), embedder=embedder)
        filters = RetrievalFilters(year_from=2021, sources=["source-b"])
        for mode in ("lexical", "dense", "hybrid"):
            retriever = HybridRetriever(world, embedder=embedder)
            response = retriever.search("retrieval", filters=filters, mode=mode, limit=10)
            assert response.hits
            assert {hit.paper_id for hit in response.hits} == {"b"}


def test_embedding_model_isolation(tmp_path: Path) -> None:
    db = tmp_path / "world.sqlite"
    paper = _paper("p1", "Dense study", 2024, "test")
    index_embedder = HashEmbeddingProvider(16)
    query_embedder = HashEmbeddingProvider(32)
    with ScientificWorldModel(db) as world:
        index_extraction(world, paper, _extraction(paper, ["semantic retrieval"]), embedder=index_embedder)
        response = HybridRetriever(world, embedder=query_embedder).search("semantic", mode="dense")
    assert response.hits == []


def test_reindex_without_embedding_preserves_existing_vector(tmp_path: Path) -> None:
    db = tmp_path / "world.sqlite"
    paper = _paper("p1", "Persistent vector", 2024, "test")
    embedder = HashEmbeddingProvider(16)
    with ScientificWorldModel(db) as world:
        extraction = _extraction(paper, ["persistent vector retrieval"])
        index_extraction(world, paper, extraction, embedder=embedder)
        before = world.connection.execute("SELECT vector, vector_model FROM chunks WHERE paper_id='p1'").fetchone()
        index_extraction(world, paper, extraction, embedder=None)
        after = world.connection.execute("SELECT vector, vector_model FROM chunks WHERE paper_id='p1'").fetchone()
    assert bytes(before["vector"]) == bytes(after["vector"])
    assert before["vector_model"] == after["vector_model"] == "hash:16"


def test_world_model_entity_ids_are_stable(tmp_path: Path) -> None:
    db = tmp_path / "world.sqlite"
    paper = _paper("p1", "Entity study", 2024, "test")
    normalized = "retrieval"
    expected = f"method:{hashlib.sha1(normalized.encode('utf-8')).hexdigest()[:20]}"
    with ScientificWorldModel(db) as world:
        index_extraction(world, paper, _extraction(paper, ["retrieval evidence"]))
        assert world.get_node(expected) is not None


def test_vector_corruption_is_detected(tmp_path: Path) -> None:
    db = tmp_path / "world.sqlite"
    paper = _paper("p1", "Corrupt vector", 2024, "test")
    embedder = HashEmbeddingProvider(16)
    with ScientificWorldModel(db) as world:
        extraction = _extraction(paper, ["corrupt vector"])
        index_extraction(world, paper, extraction, embedder=embedder)
        world.connection.execute("UPDATE chunks SET vector=? WHERE paper_id='p1'", (sqlite3.Binary(struct.pack('<f', 1.0)),))
        world.connection.commit()
        with pytest.raises(ValueError, match="Corrupt vector blob"):
            HybridRetriever(world, embedder=embedder).search("corrupt", mode="dense")


def test_graph_traversal_direction(tmp_path: Path) -> None:
    db = tmp_path / "world.sqlite"
    with ScientificWorldModel(db) as world:
        for node_id in ("a", "b", "c"):
            world.upsert_node(WorldNode(node_id=node_id, node_type="paper", paper_id=node_id, label=node_id.upper()))
        world.upsert_edge(WorldEdge(edge_id="ab", source_id="a", target_id="b", edge_type="cites"))
        world.upsert_edge(WorldEdge(edge_id="bc", source_id="b", target_id="c", edge_type="cites"))
        world.commit()
        outgoing = world.traverse("a", depth=2, edge_types={"cites"}, direction="out")
        incoming = world.traverse("c", depth=2, edge_types={"cites"}, direction="in")
    assert outgoing.node_ids == ["a", "b", "c"]
    assert incoming.node_ids == ["a", "b", "c"]
    assert outgoing.edge_ids == ["ab", "bc"]


def test_world_model_rejects_unknown_traversal_start(tmp_path: Path) -> None:
    with ScientificWorldModel(tmp_path / "world.sqlite") as world:
        with pytest.raises(ValueError, match="Unknown start node"):
            world.traverse("missing")
