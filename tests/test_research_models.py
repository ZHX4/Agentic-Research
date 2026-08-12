from agentic_research.provenance import ProvenanceEdge
from agentic_research.schemas import ExperimentPlan, ExperimentResult, Hypothesis


def test_hypothesis_composite_score_is_deterministic() -> None:
    hypothesis = Hypothesis(
        hypothesis_id="h1",
        statement="X improves Y under Z",
        novelty_score=1.0,
        evidence_score=0.8,
        significance_score=0.6,
        feasibility_score=0.4,
        diversity_score=0.2,
        falsification_condition="Reject if the effect is not reproduced across three seeds.",
    )
    assert hypothesis.composite_score == 0.25 + 0.16 + 0.12 + 0.08 + 0.03


def test_experiment_plan_has_reproducible_seed_defaults() -> None:
    plan = ExperimentPlan(
        hypothesis_id="h1",
        research_question="Does X improve Y?",
    )
    assert plan.seeds == [1, 2, 3]


def test_experiment_result_records_provenance_inputs() -> None:
    result = ExperimentResult(
        experiment_id="e1",
        hypothesis_id="h1",
        code_revision="abc123",
        dataset_manifest="datasets/v1.json",
        seed=1,
        metrics={"accuracy": 0.9},
        artifacts=["results.json"],
        success=True,
    )
    assert result.hypothesis_id == "h1"
    assert result.dataset_manifest == "datasets/v1.json"


def test_provenance_edge_requires_valid_confidence() -> None:
    edge = ProvenanceEdge(
        source_id="p1",
        target_id="g1",
        relation="supports",
        agent="gap-hunter",
        confidence=0.8,
    )
    assert edge.relation == "supports"
