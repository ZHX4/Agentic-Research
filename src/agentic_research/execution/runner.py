"""Multi-seed execution and scientific result aggregation."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

from agentic_research.execution.sandbox import DockerSandboxExecutor, SandboxViolation, environment_fingerprint
from agentic_research.schemas.phase7 import ExperimentResult, ExperimentSpec, MetricRecord, SeedRun


def _command_hash(command: list[str]) -> str:
    return hashlib.sha256(json.dumps(command, separators=(",", ":")).encode("utf-8")).hexdigest()


def _aggregate_metrics(seed_runs: list[SeedRun]) -> list[MetricRecord]:
    grouped: dict[tuple[str, str], list[MetricRecord]] = {}
    for run in seed_runs:
        for metric in run.metrics:
            grouped.setdefault((metric.name, metric.split), []).append(metric)
    return [MetricRecord(name=name, value=mean(item.value for item in values), seed=-1, split=split) for (name, split), values in sorted(grouped.items())]


def _parse_metrics(run: SeedRun, artifact_dir: Path) -> SeedRun:
    metrics_file = artifact_dir / "metrics.json"
    if not metrics_file.is_file():
        return run.model_copy(update={"status": "failed", "error": "Required metrics.json was not produced by the experiment"})
    try:
        payload = json.loads(metrics_file.read_text(encoding="utf-8"))
        if not isinstance(payload, list) or not payload:
            raise ValueError("metrics.json must contain a non-empty JSON array")
        records = [MetricRecord(name=str(item["name"]), value=float(item["value"]), seed=run.seed, split=str(item.get("split", "test"))) for item in payload]
        return run.model_copy(update={"metrics": records})
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return run.model_copy(update={"status": "failed", "error": f"Invalid metrics.json: {exc}"})


def _rejected_runs(spec: ExperimentSpec, message: str) -> list[SeedRun]:
    return [SeedRun(seed=seed, status="rejected", duration_seconds=0.0, error=message) for seed in spec.seeds]


def run_experiment(spec: ExperimentSpec, *, code_dir: Path, output_dir: Path, executor: DockerSandboxExecutor | None = None) -> ExperimentResult:
    runner = executor or DockerSandboxExecutor()
    try:
        seed_runs = runner.execute(spec, code_dir=code_dir, output_dir=output_dir)
        image_digest = runner._image_digest(spec.sandbox.image)
    except (SandboxViolation, FileNotFoundError, subprocess.CalledProcessError) as exc:
        seed_runs = _rejected_runs(spec, str(exc))
        image_digest = hashlib.sha256(spec.sandbox.image.encode("utf-8")).hexdigest()
    parsed = [_parse_metrics(run, output_dir / f"seed-{run.seed}") for run in seed_runs]
    status = "succeeded" if parsed and all(run.status == "succeeded" for run in parsed) and len(parsed) == len(spec.seeds) else "failed"
    if any(run.status == "timeout" for run in parsed):
        status = "timeout"
    if any(run.status == "rejected" for run in parsed):
        status = "rejected"
    falsified, rationale = evaluate_falsification(spec, parsed)
    environment_sha = environment_fingerprint(spec, image_digest)
    command_sha = _command_hash(spec.command)
    return ExperimentResult(
        result_id="result:" + hashlib.sha256(f"{spec.experiment_id}|{environment_sha}".encode()).hexdigest()[:20],
        experiment_id=spec.experiment_id,
        hypothesis_id=spec.hypothesis_id,
        status=status,
        seed_runs=parsed,
        aggregate_metrics=_aggregate_metrics(parsed),
        falsified=falsified,
        falsification_rationale=rationale,
        reproducible=(status == "succeeded" and _is_reproducible(parsed)),
        environment_sha256=environment_sha,
        command_sha256=command_sha,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def evaluate_falsification(spec: ExperimentSpec, runs: list[SeedRun]) -> tuple[bool | None, str | None]:
    if not runs or any(run.status != "succeeded" for run in runs):
        return None, "Falsification cannot be decided because not all seed runs succeeded."
    primary = spec.falsification.primary_metric
    values = [m.value for run in runs for m in run.metrics if m.name == primary and m.split == "test"]
    if not values:
        return None, f"Primary metric {primary!r} was not emitted by the experiment."
    threshold = spec.falsification.minimum_effect_size
    if threshold is None:
        return None, "No operational minimum_effect_size was specified; remaining rejection criteria require domain-specific review."
    if spec.falsification.metric_direction == "higher" and max(values) < threshold:
        return True, "Primary metric remained below the prespecified minimum effect size."
    if spec.falsification.metric_direction == "lower" and min(values) > threshold:
        return True, "Primary metric remained above the prespecified maximum acceptable value."
    return False, "The configured metric threshold was not crossed. This is not evidence that the hypothesis is true."


def _is_reproducible(runs: list[SeedRun]) -> bool:
    by_metric: dict[str, list[float]] = {}
    for run in runs:
        for metric in run.metrics:
            if metric.split == "test":
                by_metric.setdefault(metric.name, []).append(metric.value)
    return all(len(values) >= 2 and max(values) - min(values) <= max(1e-12, 0.10 * max(abs(v) for v in values)) for values in by_metric.values())
