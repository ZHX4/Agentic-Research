"""Deterministic experiment and falsification planning."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

from agentic_research.schemas.phase6 import Hypothesis
from agentic_research.schemas.phase7 import DatasetManifest, ExperimentSpec, FalsificationPlan, SandboxPolicy


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def build_falsification_plan(
    hypothesis: Hypothesis,
    primary_metric: str,
    alpha: float = 0.05,
    metric_direction: Literal["higher", "lower"] = "higher",
) -> FalsificationPlan:
    return FalsificationPlan(
        plan_id="falsify:" + hashlib.sha256(hypothesis.hypothesis_id.encode()).hexdigest()[:20],
        hypothesis_id=hypothesis.hypothesis_id,
        primary_metric=primary_metric,
        metric_direction=metric_direction,
        null_hypothesis=f"The proposed effect of hypothesis {hypothesis.hypothesis_id} is absent under the prespecified controls.",
        rejection_criteria=[
            hypothesis.falsification_condition,
            "Reject claimed success when the primary metric does not meet the prespecified threshold across seeds.",
        ],
        required_ablations=["remove the proposed mechanism", "remove any adjacent technique"],
        required_controls=["strongest appropriate baseline", "matched-data/control condition"],
        alpha=alpha,
        confidence_level=1.0 - alpha,
    )


def build_experiment_spec(
    hypothesis: Hypothesis,
    *,
    code_path: Path,
    command: list[str],
    datasets: list[DatasetManifest],
    primary_metric: str,
    metric_direction: Literal["higher", "lower"] = "higher",
    seeds: list[int] | None = None,
    image: str = "python:3.11-slim",
    network_enabled: bool = False,
    allow_gpu: bool = False,
    timeout_seconds: int = 3600,
) -> ExperimentSpec:
    if not command or any(not token for token in command):
        raise ValueError("command must contain non-empty argv tokens")
    if not code_path.is_file():
        raise FileNotFoundError(code_path)
    selected_seeds = sorted(set(seeds if seeds is not None else [1, 2, 3]))
    if not selected_seeds or any(seed < 0 for seed in selected_seeds):
        raise ValueError("at least one non-negative seed is required")
    code_hash = sha256_file(code_path)
    falsification = build_falsification_plan(hypothesis, primary_metric, metric_direction=metric_direction)
    experiment_id = "exp:" + hashlib.sha256(
        json.dumps(
            {
                "hypothesis_id": hypothesis.hypothesis_id,
                "code_sha256": code_hash,
                "code_path": code_path.name,
                "command": command,
                "seeds": selected_seeds,
                "metric_direction": metric_direction,
                "datasets": [dataset.dataset_id for dataset in datasets],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()[:20]
    return ExperimentSpec(
        experiment_id=experiment_id,
        hypothesis_id=hypothesis.hypothesis_id,
        research_question=hypothesis.research_question,
        command=command,
        code_path=code_path.name,
        code_sha256=code_hash,
        datasets=datasets,
        baselines=["strongest appropriate baseline", "matched control"],
        metrics=[primary_metric],
        seeds=selected_seeds,
        falsification=falsification,
        sandbox=SandboxPolicy(
            image=image,
            network_enabled=network_enabled,
            allow_gpu=allow_gpu,
            timeout_seconds=timeout_seconds,
        ),
    )
