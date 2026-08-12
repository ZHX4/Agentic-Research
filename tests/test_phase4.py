from __future__ import annotations

import hashlib
from pathlib import Path

from agentic_research.gaps import discover_gaps
from agentic_research.schemas import Paper
from agentic_research.schemas.phase3 import WorldEdge, WorldNode
from agentic_research.schemas.phase4 import GapDiscoveryConfig
from agentic_research.world_model.store import ScientificWorldModel


def _entity_node_id(kind: str, label: str) -> str:
    normalized = " ".join(label.lower().split())
    return f"{kind}:{hashlib.sha1(normalized.encode('utf-8')).hexdigest()[:20]}"


def _paper(paper_id: str, title: str, year: int, metadata: dict[str, object]) -> Paper:
    return Paper(paper_id=paper_id, title=title, year=year, metadata=metadata)


def _add_paper(world: ScientificWorldModel, paper: Paper, *, methods: list[str], datasets: list[str], tasks: list[str]) -> None:
    world.upsert_paper(paper)
    paper_node = f"paper:{paper.paper_id}"
    world.upsert_node(WorldNode(node_id=paper_node, node_type="paper", paper_id=paper.paper_id, label=paper.title))
    for field, node_type, edge_type, values in (("method", "method", "has_method", methods), ("dataset", "dataset", "has_dataset", datasets), ("task", "task", "has_task", tasks)):
        for value in values:
            node_id = _entity_node_id(field, value)
            world.upsert_node(WorldNode(node_id=node_id, node_type=node_type, label=value))
            world.upsert_edge(WorldEdge(edge_id=f"{edge_type}:{paper.paper_id}:{node_id}", source_id=paper_node, target_id=node_id, edge_type=edge_type))


def _add_claim(world: ScientificWorldModel, claim_id: str, paper_id: str, text: str, claim_type: str) -> None:
    world.upsert_node(WorldNode(node_id=claim_id, node_type="claim", paper_id=paper_id, label=text, payload={"claim_type": claim_type}))


def test_missing_combination_is_candidate_only_and_uses_real_graph_ids(tmp_path: Path) -> None:
    with ScientificWorldModel(tmp_path / "world.sqlite") as world:
        _add_paper(world, _paper("p1", "A", 2024, {"domain": "vision"}), methods=["method-a"], datasets=["dataset-a"], tasks=["task-a"])
        _add_paper(world, _paper("p2", "B", 2024, {"domain": "vision"}), methods=["method-a"], datasets=["dataset-b"], tasks=["task-a"])
        result = discover_gaps(world, GapDiscoveryConfig(include_types={"missing_combination"}, min_entity_support=1))
        signal_by_id = {signal.signal_id: signal for signal in result.signals}
        assert result.candidates
        assert all(candidate.status == "candidate" for candidate in result.candidates)
        assert all(not candidate.counterevidence_ids for candidate in result.candidates)
        for candidate in result.candidates:
            signal = signal_by_id[candidate.signal_ids[0]]
            assert signal.node_ids
            assert all(world.get_node(node_id) is not None for node_id in signal.node_ids)


def test_method_task_missing_combination_is_found(tmp_path: Path) -> None:
    with ScientificWorldModel(tmp_path / "world.sqlite") as world:
        _add_paper(world, _paper("m", "Method paper", 2024, {}), methods=["method-a"], datasets=["dataset-x"], tasks=["task-a"])
        _add_paper(world, _paper("t", "Task paper", 2024, {}), methods=["method-b"], datasets=["dataset-x"], tasks=["task-b"])
        result = discover_gaps(world, GapDiscoveryConfig(include_types={"missing_combination"}, min_entity_support=1))
    assert any(candidate.method == "method-a" and candidate.task == "task-b" for candidate in result.candidates)


def test_contradiction_requires_distinct_result_papers(tmp_path: Path) -> None:
    with ScientificWorldModel(tmp_path / "world.sqlite") as world:
        _add_paper(world, _paper("p1", "Positive", 2024, {}), methods=[], datasets=[], tasks=[])
        _add_paper(world, _paper("p2", "Negative", 2024, {}), methods=[], datasets=[], tasks=[])
        _add_claim(world, "c1", "p1", "method improves factual accuracy", "result")
        _add_claim(world, "c2", "p2", "method decreases factual accuracy", "result")
        result = discover_gaps(world, GapDiscoveryConfig(include_types={"contradiction"}))
    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.gap_type == "contradiction"
    assert set(candidate.evidence_paper_ids) == {"p1", "p2"}
    assert candidate.status == "candidate"


def test_negated_improvement_is_not_marked_positive(tmp_path: Path) -> None:
    with ScientificWorldModel(tmp_path / "world.sqlite") as world:
        _add_paper(world, _paper("p1", "Negative", 2024, {}), methods=[], datasets=[], tasks=[])
        _add_paper(world, _paper("p2", "Negative 2", 2024, {}), methods=[], datasets=[], tasks=[])
        _add_claim(world, "c1", "p1", "method does not improve factual accuracy", "result")
        _add_claim(world, "c2", "p2", "method does not improve factual accuracy", "result")
        result = discover_gaps(world, GapDiscoveryConfig(include_types={"contradiction"}))
    assert result.candidates == []


def test_recurring_limitation_creates_candidate(tmp_path: Path) -> None:
    with ScientificWorldModel(tmp_path / "world.sqlite") as world:
        for paper_id in ("p1", "p2"):
            _add_paper(world, _paper(paper_id, paper_id, 2024, {}), methods=[], datasets=[], tasks=[])
        _add_claim(world, "l1", "p1", "limited multilingual evaluation", "limitation")
        _add_claim(world, "l2", "p2", "limited multilingual evaluation", "limitation")
        result = discover_gaps(world, GapDiscoveryConfig(include_types={"unresolved_limitation"}))
    assert len(result.candidates) == 1
    assert result.candidates[0].gap_type == "unresolved_limitation"
    assert result.candidates[0].support_count == 2


def test_underexplored_condition_is_detected(tmp_path: Path) -> None:
    with ScientificWorldModel(tmp_path / "world.sqlite") as world:
        for paper_id in ("p1", "p2", "p3", "p4", "p5"):
            condition = "arabic" if paper_id == "p1" else "english"
            _add_paper(world, _paper(paper_id, paper_id, 2024, {"language": condition}), methods=["method-a"], datasets=[], tasks=["task-a"])
        result = discover_gaps(world, GapDiscoveryConfig(include_types={"underexplored_condition"}, min_entity_support=2, min_condition_support=2))
    assert any(candidate.gap_type == "underexplored_condition" for candidate in result.candidates)


def test_cross_domain_candidate_needs_missing_direct_combination(tmp_path: Path) -> None:
    with ScientificWorldModel(tmp_path / "world.sqlite") as world:
        _add_paper(world, _paper("p1", "Vision", 2024, {"domain": "computer vision"}), methods=["method-a"], datasets=[], tasks=[])
        _add_paper(world, _paper("p2", "NLP", 2024, {"domain": "natural language processing"}), methods=[], datasets=[], tasks=["task-b"])
        result = discover_gaps(world, GapDiscoveryConfig(include_types={"cross_domain"}, min_entity_support=1))
    assert all(candidate.status == "candidate" for candidate in result.candidates)
    assert any(candidate.gap_type == "cross_domain" for candidate in result.candidates)


def test_graph_negative_space_uses_common_task_neighbors(tmp_path: Path) -> None:
    with ScientificWorldModel(tmp_path / "world.sqlite") as world:
        _add_paper(world, _paper("m1", "Method One A", 2024, {}), methods=["method-a"], datasets=[], tasks=["task-1"])
        _add_paper(world, _paper("m2", "Method One B", 2024, {}), methods=["method-a"], datasets=[], tasks=["task-2"])
        _add_paper(world, _paper("d1", "Dataset One A", 2024, {}), methods=[], datasets=["dataset-z"], tasks=["task-1"])
        _add_paper(world, _paper("d2", "Dataset One B", 2024, {}), methods=[], datasets=["dataset-z"], tasks=["task-2"])
        result = discover_gaps(world, GapDiscoveryConfig(include_types={"graph_negative_space"}, min_graph_degree=2, min_common_neighbors=2))
    assert result.candidates
    assert all(candidate.gap_type == "graph_negative_space" for candidate in result.candidates)


def test_temporal_cutoff_excludes_future_papers(tmp_path: Path) -> None:
    with ScientificWorldModel(tmp_path / "world.sqlite") as world:
        _add_paper(world, _paper("old", "Old", 2020, {}), methods=["method-a"], datasets=["dataset-a"], tasks=["task-a"])
        _add_paper(world, _paper("future", "Future", 2026, {}), methods=["method-b"], datasets=["dataset-b"], tasks=["task-b"])
        result = discover_gaps(world, GapDiscoveryConfig(include_types={"missing_combination"}, min_entity_support=1, temporal_cutoff=2022))
    assert result.corpus_paper_count == 1
    assert all("future" not in candidate.evidence_paper_ids for candidate in result.candidates)


def test_run_id_changes_when_indexed_content_changes(tmp_path: Path) -> None:
    db = tmp_path / "world.sqlite"
    with ScientificWorldModel(db) as world:
        _add_paper(world, _paper("p1", "A", 2024, {}), methods=["method-a"], datasets=["dataset-a"], tasks=["task-a"])
        config = GapDiscoveryConfig(include_types={"missing_combination"}, min_entity_support=1)
        first = discover_gaps(world, config)
        _add_paper(world, _paper("p2", "B", 2024, {}), methods=["method-b"], datasets=["dataset-b"], tasks=["task-a"])
        second = discover_gaps(world, config)
    assert first.run_id != second.run_id
