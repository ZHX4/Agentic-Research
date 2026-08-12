import hashlib
from pathlib import Path

import pytest

from agentic_research.execution.planner import build_experiment_spec, sha256_file
from agentic_research.execution.runner import evaluate_falsification
from agentic_research.execution.sandbox import DockerSandboxExecutor, SandboxViolation
from agentic_research.execution.tree import append_result, create_tree
from agentic_research.schemas.phase6 import Hypothesis
from agentic_research.schemas.phase7 import ArtifactRecord, DatasetManifest, ExperimentResult, ExperimentSpec, FalsificationPlan, MetricRecord, SandboxPolicy, SeedRun


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
    dataset = DatasetManifest(dataset_id="d1", name="Demo", version="1", source="local", sha256=hashlib.sha256(b"dataset").hexdigest(), immutable=True)
    a = build_experiment_spec(make_hypothesis(), code_path=code, command=["python", "run.py"], datasets=[dataset], primary_metric="accuracy", seeds=[3, 1, 2])
    b = build_experiment_spec(make_hypothesis(), code_path=code, command=["python", "run.py"], datasets=[dataset], primary_metric="accuracy", seeds=[1, 2, 3])
    assert a.experiment_id == b.experiment_id
    assert a.code_sha256 == sha256_file(code)
    assert a.code_path == "run.py"
    assert a.seeds == [1, 2, 3]


def test_experiment_rejects_duplicate_seed(tmp_path: Path) -> None:
    code = tmp_path / "run.py"
    code.write_text("print('ok')", encoding="utf-8")
    with pytest.raises(ValueError):
        build_experiment_spec(make_hypothesis(), code_path=code, command=["python", "run.py"], datasets=[], primary_metric="accuracy", seeds=[1, 1])


def test_sandbox_policy_defaults_to_safe_execution() -> None:
    policy = SandboxPolicy(image="python:3.11-slim")
    assert policy.network_enabled is False
    assert policy.read_only_root is True
    assert policy.allow_gpu is False


def test_sandbox_rejects_forbidden_docker_flags() -> None:
    executor = DockerSandboxExecutor()
    with pytest.raises(SandboxViolation):
        executor._validate_command(["--privileged"])
    with pytest.raises(SandboxViolation):
        executor._validate_command(["-v", "/host:/container"])


def _experiment_with_direction(direction: str, threshold: float) -> ExperimentSpec:
    hypothesis = make_hypothesis()
    return ExperimentSpec(
        experiment_id="e1",
        hypothesis_id=hypothesis.hypothesis_id,
        research_question=hypothesis.research_question,
        command=["python", "run.py"],
        code_path="run.py",
        code_sha256=hashlib.sha256(b"code").hexdigest(),
        datasets=[],
        metrics=["score"],
        seeds=[1, 2],
        falsification=FalsificationPlan(
            plan_id="f1",
            hypothesis_id=hypothesis.hypothesis_id,
            primary_metric="score",
            metric_direction=direction,
            null_hypothesis="none",
            rejection_criteria=["threshold"],
            minimum_effect_size=threshold,
        ),
        sandbox=SandboxPolicy(image="python:3.11-slim"),
    )


def test_falsification_uses_higher_direction() -> None:
    spec = _experiment_with_direction("higher", 0.8)
    runs = [SeedRun(seed=1, status="succeeded", duration_seconds=1, metrics=[MetricRecord(name="score", value=0.7, seed=1, split="test")]), SeedRun(seed=2, status="succeeded", duration_seconds=1, metrics=[MetricRecord(name="score", value=0.75, seed=2, split="test")])]
    falsified, rationale = evaluate_falsification(spec, runs)
    assert falsified is True
    assert rationale


def test_falsification_uses_lower_direction() -> None:
    spec = _experiment_with_direction("lower", 0.2)
    runs = [SeedRun(seed=1, status="succeeded", duration_seconds=1, metrics=[MetricRecord(name="score", value=0.3, seed=1, split="test")]), SeedRun(seed=2, status="succeeded", duration_seconds=1, metrics=[MetricRecord(name="score", value=0.25, seed=2, split="test")])]
    falsified, rationale = evaluate_falsification(spec, runs)
    assert falsified is True
    assert rationale


def test_falsification_without_operational_threshold_is_inconclusive() -> None:
    spec = _experiment_with_direction("higher", 0.8).model_copy(update={"falsification": _experiment_with_direction("higher", 0.8).falsification.model_copy(update={"minimum_effect_size": None})})
    runs = [SeedRun(seed=1, status="succeeded", duration_seconds=1, metrics=[MetricRecord(name="score", value=0.1, seed=1, split="test")]), SeedRun(seed=2, status="succeeded", duration_seconds=1, metrics=[MetricRecord(name="score", value=0.2, seed=2, split="test")])]
    falsified, _ = evaluate_falsification(spec, runs)
    assert falsified is None


def test_experiment_spec_rejects_path_escape() -> None:
    with pytest.raises(ValueError):
        _experiment_with_direction("higher", 0.8).model_copy(update={"code_path": "../run.py"})


def test_experiment_tree_integrity() -> None:
    spec = _experiment_with_direction("higher", 0.8)
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
