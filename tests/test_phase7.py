import hashlib
from pathlib import Path

import pytest

from agentic_research.execution.planner import build_experiment_spec, sha256_file
from agentic_research.execution.runner import evaluate_falsification
from agentic_research.execution.sandbox import DockerSandboxExecutor, SandboxViolation
from agentic_research.execution.tree import append_result, create_tree
from agentic_research.schemas.phase6 import Hypothesis
from agentic_research.schemas.phase7 import (
    ArtifactRecord,
    DatasetManifest,
    ExperimentResult,
    FalsificationPlan,
    MetricRecord,
    SandboxPolicy,
    SeedRun,
)


def make_hypothesis() -> Hypothesis:
    return Hypothesis(
        hypothesis_id="hyp-1",
        statement="Method M improves Task T on Dataset D under controls.",
        research_question="Does M improve T on D?",
        source_gap_ids=["gap-1"],
        source_statuses=["survived"],
        origin="gap_direct",
        mechanism="Apply M to D",
        expected_effect="higher score",
        falsification_condition="reject when no improvement is observed",
        assumptions=["valid baseline"],
        predicted_observations=["stable across seeds"],
        novelty_score=0.8,
        evidence_score=0.8,
        significance_score=0.8,
        feasibility_score=0.8,
        diversity_score=0.8,
        robustness_score=0.8,
        reflection_score=0.8,
    )


def test_experiment_plan_is_deterministic(tmp_path: Path) -> None:
    code = tmp_path / "run.py"
    code.write_text("print('ok')", encoding="utf-8")
    dataset = DatasetManifest(
        dataset_id="d1",
        name="Demo",
        version="1",
        source="local",
        sha256=hashlib.sha256(b"dataset").hexdigest(),
        immutable=True,
    )
    a = build_experiment_spec(make_hypothesis(), code_path=code, command=["python", "run.py"], datasets=[dataset], primary_metric="accuracy", seeds=[3, 1, 2])
    b = build_experiment_spec(make_hypothesis(), code_path=code, command=["python", "run.py"], datasets=[dataset], primary_metric="accuracy", seeds=[1, 2, 3])
    assert a.experiment_id == b.experiment_id
    assert a.code_sha256 == sha256_file(code)
    assert a.seeds == [1, 2, 3]


def test_experiment_rejects_duplicate_seed() -> None:
    with pytest.raises(ValueError):
        build_experiment_spec(
            make_hypothesis(),
            code_path=Path(__file__),
            command=["python", "x.py"],
            datasets=[],
            primary_metric="accuracy",
            seeds=[1, 1],
        )


def test_sandbox_policy_defaults_to_safe_execution() -> None:
    policy = SandboxPolicy(image="python:3.11-slim")
    assert policy.network_enabled is False
    assert policy.read_only_root is True
    assert policy.allow_gpu is False


def test_sandbox_rejects_forbidden_docker_flags() -> None:
    executor = DockerSandboxExecutor()
    with pytest.raises(SandboxViolation):
        executor._validate_command(["--privileged"])


def test_falsification_uses_explicit_threshold() -> None:
    hypothesis = make_hypothesis()
    plan = FalsificationPlan(
        plan_id="f1",
        hypothesis_id=hypothesis.hypothesis_id,
        primary_metric="accuracy",
        null_hypothesis="no improvement",
        rejection_criteria=["accuracy below threshold"],
        minimum_effect_size=0.8,
    )
    from agentic_research.schemas.phase7 import ExperimentSpec
    spec = ExperimentSpec(
        experiment_id="e1",
        hypothesis_id=hypothesis.hypothesis_id,
        research_question=hypothesis.research_question,
        command=["python", "run.py"],
        code_sha256=hashlib.sha256(b"code").hexdigest(),
        datasets=[],
        metrics=["accuracy"],
        seeds=[1, 2],
        falsification=plan,
        sandbox=SandboxPolicy(image="python:3.11-slim"),
    )
    runs = [
        SeedRun(seed=1, status="succeeded", duration_seconds=1, metrics=[MetricRecord(name="accuracy", value=0.7, seed=1, split="test")]),
        SeedRun(seed=2, status="succeeded", duration_seconds=1, metrics=[MetricRecord(name="accuracy", value=0.75, seed=2, split="test")]),
    ]
    falsified, rationale = evaluate_falsification(spec, runs)
    assert falsified is True
    assert rationale


def test_experiment_tree_integrity() -> None:
    from agentic_research.schemas.phase7 import ExperimentSpec
    spec = ExperimentSpec(
        experiment_id="e1",
        hypothesis_id="hyp-1",
        research_question="question",
        command=["python", "run.py"],
        code_sha256=hashlib.sha256(b"code").hexdigest(),
        datasets=[],
        metrics=["accuracy"],
        seeds=[1],
        falsification=FalsificationPlan(
            plan_id="f1",
            hypothesis_id="hyp-1",
            primary_metric="accuracy",
            null_hypothesis="none",
            rejection_criteria=["fail"],
        ),
        sandbox=SandboxPolicy(image="python:3.11-slim"),
    )
    tree = create_tree(spec)
    result = ExperimentResult(
        result_id="r1",
        experiment_id="e1",
        hypothesis_id="hyp-1",
        status="failed",
        seed_runs=[SeedRun(seed=1, status="failed", duration_seconds=1, artifacts=[ArtifactRecord(artifact_id="a1", relative_path="x", sha256=hashlib.sha256(b"x").hexdigest(), byte_size=1, media_type="text/plain")])],
        environment_sha256=hashlib.sha256(b"env").hexdigest(),
        command_sha256=hashlib.sha256(b"cmd").hexdigest(),
        created_at="2026-01-01T00:00:00+00:00",
    )
    updated = append_result(tree, result)
    assert updated.nodes[-1].result_id == "r1"
    assert updated.terminal_node_ids == [updated.nodes[-1].node_id]
