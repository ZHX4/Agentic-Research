from agentic_research.provenance import ProvenanceEdge
from agentic_research.schemas import ExperimentPlan, ExperimentResult, Hypothesis
from agentic_research.schemas.phase7 import SeedRun


def test_hypothesis_composite_score_is_deterministic() -> None:
    hypothesis = Hypothesis(
        hypothesis_id="h1",
        statement="X improves Y under Z",
        research_question="Does X improve Y?",
        origin="gap_direct",
        mechanism="Apply X",
        expected_effect="higher score",
        novelty_score=1.0,
        evidence_score=0.8,
        significance_score=0.6,
        feasibility_score=0.4,
        diversity_score=0.2,
        robustness_score=0.5,
        reflection_score=0.5,
        falsification_condition="Reject if the effect is not reproduced across three seeds.",
    )
    assert hypothesis.composite_score == 0.22 + 0.128 + 0.102 + 0.068 + 0.02 + 0.05 + 0.04


def test_experiment_plan_has_reproducible_seed_defaults() -> None:
    plan = ExperimentPlan(
        hypothesis_id="h1",
        research_question="Does X improve Y?",
    )
    assert plan.seeds == [1, 2, 3]


def test_experiment_result_records_provenance_inputs() -> None:
    result = ExperimentResult(
        result_id="r1",
        experiment_id="e1",
        hypothesis_id="h1",
        status="succeeded",
        seed_runs=[
            SeedRun(seed=1, status="succeeded", duration_seconds=1.0),
        ],
        environment_sha256="a" * 64,
        command_sha256="b" * 64,
        created_at="2026-01-01T00:00:00+00:00",
    )
    assert result.hypothesis_id == "h1"
    assert result.experiment_id == "e1"


def test_provenance_edge_requires_valid_confidence() -> None:
    edge = ProvenanceEdge(
        source_id="p1",
        target_id="g1",
        relation="supports",
        agent="gap-hunter",
        confidence=0.8,
    )
    assert edge.relation == "supports"
