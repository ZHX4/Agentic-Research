import hashlib
import json
import subprocess
from pathlib import Path
from typing import Literal

import pytest

from agentic_research.execution.planner import build_experiment_spec, sha256_file
from agentic_research.execution.runner import evaluate_falsification, run_experiment
from agentic_research.execution.sandbox import (
    DockerSandboxExecutor,
    SandboxViolation,
    environment_fingerprint,
)
from agentic_research.execution.tree import append_result, create_tree
from agentic_research.schemas.gap import GapStatus
from agentic_research.schemas.phase6 import Hypothesis
from agentic_research.schemas.phase7 import (
    ArtifactRecord,
    DatasetManifest,
    ExperimentResult,
    ExperimentSpec,
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
        source_statuses=[GapStatus.SURVIVED],
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
    a = build_experiment_spec(
        make_hypothesis(),
        code_path=code,
        command=["python", "run.py"],
        datasets=[dataset],
        primary_metric="accuracy",
        seeds=[3, 1, 2],
    )
    b = build_experiment_spec(
        make_hypothesis(),
        code_path=code,
        command=["python", "run.py"],
        datasets=[dataset],
        primary_metric="accuracy",
        seeds=[1, 2, 3],
    )
    assert a.experiment_id == b.experiment_id
    assert a.code_sha256 == sha256_file(code)
    assert a.code_path == "run.py"
    assert a.seeds == [1, 2, 3]


def test_experiment_rejects_duplicate_seed(tmp_path: Path) -> None:
    code = tmp_path / "run.py"
    code.write_text("print('ok')", encoding="utf-8")
    with pytest.raises(ValueError):
        build_experiment_spec(
            make_hypothesis(),
            code_path=code,
            command=["python", "run.py"],
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
    with pytest.raises(SandboxViolation):
        executor._validate_command(["-v", "/host:/container"])


def _experiment_with_direction(
    direction: Literal["higher", "lower"], threshold: float
) -> ExperimentSpec:
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
    runs = [
        SeedRun(
            seed=1,
            status="succeeded",
            duration_seconds=1,
            metrics=[MetricRecord(name="score", value=0.7, seed=1, split="test")],
        ),
        SeedRun(
            seed=2,
            status="succeeded",
            duration_seconds=1,
            metrics=[MetricRecord(name="score", value=0.75, seed=2, split="test")],
        ),
    ]
    falsified, rationale = evaluate_falsification(spec, runs)
    assert falsified is True
    assert rationale


def test_falsification_uses_lower_direction() -> None:
    spec = _experiment_with_direction("lower", 0.2)
    runs = [
        SeedRun(
            seed=1,
            status="succeeded",
            duration_seconds=1,
            metrics=[MetricRecord(name="score", value=0.3, seed=1, split="test")],
        ),
        SeedRun(
            seed=2,
            status="succeeded",
            duration_seconds=1,
            metrics=[MetricRecord(name="score", value=0.25, seed=2, split="test")],
        ),
    ]
    falsified, rationale = evaluate_falsification(spec, runs)
    assert falsified is True
    assert rationale


def test_falsification_without_operational_threshold_is_inconclusive() -> None:
    spec = _experiment_with_direction("higher", 0.8).model_copy(
        update={
            "falsification": _experiment_with_direction("higher", 0.8).falsification.model_copy(
                update={"minimum_effect_size": None}
            )
        }
    )
    runs = [
        SeedRun(
            seed=1,
            status="succeeded",
            duration_seconds=1,
            metrics=[MetricRecord(name="score", value=0.1, seed=1, split="test")],
        ),
        SeedRun(
            seed=2,
            status="succeeded",
            duration_seconds=1,
            metrics=[MetricRecord(name="score", value=0.2, seed=2, split="test")],
        ),
    ]
    falsified, _ = evaluate_falsification(spec, runs)
    assert falsified is None


def test_experiment_spec_rejects_path_escape() -> None:
    spec = _experiment_with_direction("higher", 0.8)
    with pytest.raises(ValueError):
        ExperimentSpec.model_validate({**spec.model_dump(), "code_path": "../run.py"})


def test_experiment_tree_integrity() -> None:
    spec = _experiment_with_direction("higher", 0.8)
    tree = create_tree(spec)
    result = ExperimentResult(
        result_id="r1",
        experiment_id="e1",
        hypothesis_id="hyp-1",
        status="failed",
        seed_runs=[
            SeedRun(
                seed=1,
                status="failed",
                duration_seconds=1,
                artifacts=[
                    ArtifactRecord(
                        artifact_id="a1",
                        relative_path="x",
                        sha256=hashlib.sha256(b"x").hexdigest(),
                        byte_size=1,
                        media_type="text/plain",
                    )
                ],
            )
        ],
        environment_sha256=hashlib.sha256(b"env").hexdigest(),
        command_sha256=hashlib.sha256(b"cmd").hexdigest(),
        created_at="2026-01-01T00:00:00+00:00",
    )
    updated = append_result(tree, result)
    assert updated.nodes[-1].result_id == "r1"
    assert updated.terminal_node_ids == [updated.nodes[-1].node_id]


class _StubExecutor(DockerSandboxExecutor):
    """Overrides only the Docker boundary; real orchestration logic still runs."""

    def __init__(self, runs: list[SeedRun]) -> None:
        super().__init__()
        self._stub_runs = runs

    def execute(self, spec: ExperimentSpec, *, code_dir: Path, output_dir: Path) -> list[SeedRun]:
        return self._stub_runs

    def _image_digest(self, image: str) -> str:
        return "0" * 64


def _spec_with_dataset(tmp_path: Path) -> tuple[ExperimentSpec, Path, Path]:
    code = tmp_path / "run.py"
    code.write_text("print('ok')\n", encoding="utf-8")
    data = tmp_path / "data.bin"
    data.write_bytes(b"e2e-data")
    manifest = DatasetManifest(
        dataset_id="d1",
        name="Demo",
        version="1",
        source="local",
        sha256=hashlib.sha256(b"e2e-data").hexdigest(),
        local_path=str(data),
    )
    spec = build_experiment_spec(
        make_hypothesis(),
        code_path=code,
        command=["python", "run.py"],
        datasets=[manifest],
        primary_metric="accuracy",
    )
    return spec, tmp_path, data


def _ok_completed() -> subprocess.CompletedProcess[bytes]:
    # The main sandbox run uses bytes mode; only `docker image inspect`
    # (_image_digest, mocked in these tests) runs with text=True.
    return subprocess.CompletedProcess(args=["docker"], returncode=0, stdout=b"out", stderr=b"")


def test_sandbox_argv_enforces_restricted_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, code_dir, _ = _spec_with_dataset(tmp_path)
    captured: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        captured.append(command)
        return _ok_completed()

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(DockerSandboxExecutor, "_image_digest", lambda self, image: "0" * 64)
    run = DockerSandboxExecutor().execute_seed(
        spec, seed=1, code_dir=code_dir, artifact_dir=tmp_path / "art"
    )
    assert run.status == "succeeded"
    assert len(captured) == 1
    argv = captured[0]
    assert argv[:3] == ["docker", "run", "--rm"]
    assert "--read-only" in argv
    assert argv[argv.index("--network") + 1] == "none"
    assert argv[argv.index("--cap-drop") + 1] == "ALL"
    assert "no-new-privileges:true" in argv
    assert f"{code_dir}:{spec.sandbox.workdir}:ro" in argv
    assert any(part.endswith(":/outputs:rw") for part in argv)
    assert "AGENTIC_RESEARCH_SEED=1" in argv
    assert "AGENTIC_RESEARCH_OUTPUT_DIR=/outputs" in argv
    assert spec.sandbox.image in argv
    assert argv[-2:] == ["python", "run.py"]
    assert "--gpus" not in argv


def test_code_hash_mismatch_blocks_before_docker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, code_dir, _ = _spec_with_dataset(tmp_path)
    (code_dir / "run.py").write_text("print('tampered')\n", encoding="utf-8")
    called: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        called.append(command)
        return _ok_completed()

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(SandboxViolation, match="Code SHA-256"):
        DockerSandboxExecutor().execute_seed(
            spec, seed=1, code_dir=code_dir, artifact_dir=tmp_path / "art"
        )
    assert called == []


def test_dataset_hash_mismatch_blocks_before_docker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, code_dir, data = _spec_with_dataset(tmp_path)
    data.write_bytes(b"tampered-data")
    called: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        called.append(command)
        return _ok_completed()

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(DockerSandboxExecutor, "_image_digest", lambda self, image: "0" * 64)
    with pytest.raises(SandboxViolation, match="Dataset SHA-256"):
        DockerSandboxExecutor().execute_seed(
            spec, seed=1, code_dir=code_dir, artifact_dir=tmp_path / "art"
        )
    assert called == []


def test_missing_dataset_path_blocks_before_docker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, code_dir, data = _spec_with_dataset(tmp_path)
    data.unlink()
    called: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        called.append(command)
        return _ok_completed()

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(DockerSandboxExecutor, "_image_digest", lambda self, image: "0" * 64)
    with pytest.raises(SandboxViolation, match="does not exist"):
        DockerSandboxExecutor().execute_seed(
            spec, seed=1, code_dir=code_dir, artifact_dir=tmp_path / "art"
        )
    assert called == []


def test_nonzero_exit_is_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    spec, code_dir, _ = _spec_with_dataset(tmp_path)

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(
            args=command, returncode=1, stdout=b"out", stderr=b"boom"
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(DockerSandboxExecutor, "_image_digest", lambda self, image: "0" * 64)
    run = DockerSandboxExecutor().execute_seed(
        spec, seed=1, code_dir=code_dir, artifact_dir=tmp_path / "art"
    )
    assert run.status == "failed"
    assert run.exit_code == 1


def test_timeout_is_reported_as_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    spec, code_dir, _ = _spec_with_dataset(tmp_path)

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        raise subprocess.TimeoutExpired(command, 3600)

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(DockerSandboxExecutor, "_image_digest", lambda self, image: "0" * 64)
    run = DockerSandboxExecutor().execute_seed(
        spec, seed=1, code_dir=code_dir, artifact_dir=tmp_path / "art"
    )
    assert run.status == "timeout"
    assert run.error is not None and "3600" in run.error


def _write_metrics(output_dir: Path, seed: int, value: float, name: str = "accuracy") -> None:
    seed_dir = output_dir / f"seed-{seed}"
    seed_dir.mkdir(parents=True, exist_ok=True)
    seed_dir.joinpath("metrics.json").write_text(
        json.dumps([{"name": name, "value": value, "split": "test"}]),
        encoding="utf-8",
    )


def _succeeded_run(seed: int) -> SeedRun:
    return SeedRun(seed=seed, status="succeeded", duration_seconds=1.0)


def test_run_experiment_aggregates_success(
    tmp_path: Path,
) -> None:
    spec, code_dir, _ = _spec_with_dataset(tmp_path)
    output_dir = tmp_path / "out"
    _write_metrics(output_dir, 1, 0.80)
    _write_metrics(output_dir, 2, 0.82)
    _write_metrics(output_dir, 3, 0.81)
    result = run_experiment(
        spec,
        code_dir=code_dir,
        output_dir=output_dir,
        executor=_StubExecutor([_succeeded_run(1), _succeeded_run(2), _succeeded_run(3)]),
    )
    assert result.status == "succeeded"
    assert result.falsified is None
    assert result.reproducible is True
    assert result.environment_sha256 == environment_fingerprint(spec, "0" * 64)
    aggregate = {metric.name: metric.value for metric in result.aggregate_metrics}
    assert aggregate["accuracy"] == pytest.approx(0.81)


def test_run_experiment_missing_metrics_is_failure(tmp_path: Path) -> None:
    spec, code_dir, _ = _spec_with_dataset(tmp_path)
    output_dir = tmp_path / "out"
    output_dir.mkdir(parents=True, exist_ok=True)
    result = run_experiment(
        spec, code_dir=code_dir, output_dir=output_dir, executor=_StubExecutor([_succeeded_run(1)])
    )
    assert result.status == "failed"
    assert "metrics.json" in (result.seed_runs[0].error or "")


def test_run_experiment_malformed_metrics_is_failure(tmp_path: Path) -> None:
    spec, code_dir, _ = _spec_with_dataset(tmp_path)
    output_dir = tmp_path / "out" / "seed-1"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_dir.joinpath("metrics.json").write_text("{not json", encoding="utf-8")
    result = run_experiment(
        spec,
        code_dir=code_dir,
        output_dir=tmp_path / "out",
        executor=_StubExecutor([_succeeded_run(1)]),
    )
    assert result.status == "failed"


def test_run_experiment_partial_failure_is_not_success(tmp_path: Path) -> None:
    spec, code_dir, _ = _spec_with_dataset(tmp_path)
    output_dir = tmp_path / "out"
    _write_metrics(output_dir, 1, 0.80)
    failed = SeedRun(seed=2, status="failed", duration_seconds=1.0, error="boom")
    result = run_experiment(
        spec,
        code_dir=code_dir,
        output_dir=output_dir,
        executor=_StubExecutor([_succeeded_run(1), failed]),
    )
    assert result.status == "failed"
    assert result.falsified is None


def test_run_experiment_applies_falsification_threshold(tmp_path: Path) -> None:
    spec = _experiment_with_direction("higher", 0.8)
    output_dir = tmp_path / "out"
    _write_metrics(output_dir, 1, 0.50, name="score")
    _write_metrics(output_dir, 2, 0.55, name="score")
    result = run_experiment(
        spec,
        code_dir=tmp_path,
        output_dir=output_dir,
        executor=_StubExecutor([_succeeded_run(1), _succeeded_run(2)]),
    )
    assert result.status == "succeeded"
    assert result.falsified is True
