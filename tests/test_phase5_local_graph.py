import hashlib
from pathlib import Path

from agentic_research.schemas import GapCandidate
from agentic_research.schemas.gap import GapStatus
from agentic_research.schemas.phase3 import WorldEdge, WorldNode
from agentic_research.schemas.phase5 import NoveltyVerificationConfig
from agentic_research.verification import NoveltyVerifier
from agentic_research.world_model.store import ScientificWorldModel


def _candidate() -> GapCandidate:
    return GapCandidate(
        gap_id="local-gap",
        gap_type="missing_combination",
        statement="Method Alpha on Dataset Beta for Task Gamma is absent.",
        method="Method Alpha",
        dataset="Dataset Beta",
        task="Task Gamma",
        evidence_paper_ids=["p-support"],
        signal_ids=["signal"],
        support_count=1,
        structural_support=0.5,
        confidence=0.5,
        status=GapStatus.CANDIDATE,
        rationale="candidate",
    )


def _entity_id(kind: str, value: str) -> str:
    normalized = " ".join(value.casefold().split())
    return f"{kind}:{hashlib.sha1(normalized.encode('utf-8')).hexdigest()[:20]}"


def test_local_world_graph_exact_match_is_disproof(tmp_path: Path) -> None:
    with ScientificWorldModel(tmp_path / "world.sqlite") as world:
        world.upsert_paper(__import__("agentic_research.schemas", fromlist=["Paper"]).Paper(paper_id="prior", title="Prior", year=2024))
        paper_node = "paper:prior"
        world.upsert_node(WorldNode(node_id=paper_node, node_type="paper", paper_id="prior", label="Prior"))
        for value, kind, edge_type in (
            ("Method Alpha", "method", "has_method"),
            ("Dataset Beta", "dataset", "has_dataset"),
            ("Task Gamma", "task", "has_task"),
        ):
            node_id = _entity_id(kind, value)
            world.upsert_node(WorldNode(node_id=node_id, node_type=kind, label=value))
            world.upsert_edge(WorldEdge(edge_id=f"{edge_type}:prior:{node_id}", source_id=paper_node, target_id=node_id, edge_type=edge_type))
        world.upsert_chunk(
            chunk_id="prior-chunk",
            paper_id="prior",
            title="Prior",
            text="Method Alpha evaluates Dataset Beta for Task Gamma.",
            section="Experiments",
            page_start=1,
            page_end=1,
            year=2024,
            source="local",
            vector=None,
            vector_model=None,
        )
        world.commit()
        result = NoveltyVerifier(world=world).verify(
            _candidate(),
            NoveltyVerificationConfig(include_local=True, include_external=False),
        )

    assert result.verdict == "disproved"
    assert result.resulting_status == GapStatus.DISPROVED
    assert any(item.severity == "high" for item in result.counterevidence)
