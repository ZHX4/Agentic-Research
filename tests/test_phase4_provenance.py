from agentic_research.schemas.phase4 import GapSignal


def test_entity_values_are_kept_separate_from_unresolved_node_ids() -> None:
    signal = GapSignal(
        signal_id="s1",
        gap_type="missing_combination",
        statement="candidate",
        paper_ids=["p1"],
        node_ids=["method:unknown", "claim:known"],
        entity_values={"method": "Neural Method", "dataset": "Dataset A"},
        support_count=2,
        structural_score=0.5,
    )

    assert signal.entity_values == {"method": "Neural Method", "dataset": "Dataset A"}
    assert signal.node_ids == ["claim:known"]


def test_claim_node_ids_are_preserved() -> None:
    signal = GapSignal(
        signal_id="s2",
        gap_type="contradiction",
        statement="conflicting claims",
        paper_ids=["p1", "p2"],
        node_ids=["claim:c1", "claim:c2"],
        support_count=2,
        structural_score=0.5,
    )

    assert signal.node_ids == ["claim:c1", "claim:c2"]
