"""Composition and validation of Phase 8 evaluation reports."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agentic_research.schemas.phase8 import AblationResult, BaselineComparison, BenchmarkResult, CostRecord, EvaluationReport, HumanEvaluationResult


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report(system_name: str, *, benchmark_files: list[Path], human_files: list[Path] | None = None, baseline_files: list[Path] | None = None, ablation_files: list[Path] | None = None, cost_files: list[Path] | None = None) -> EvaluationReport:
    benchmarks = [BenchmarkResult.model_validate(_load(path)) for path in benchmark_files]
    humans = [HumanEvaluationResult.model_validate(_load(path)) for path in (human_files or [])]
    baselines = [BaselineComparison.model_validate(_load(path)) for path in (baseline_files or [])]
    ablations = [AblationResult.model_validate(_load(path)) for path in (ablation_files or [])]
    costs: list[CostRecord] = []
    for path in cost_files or []:
        payload = _load(path)
        if not isinstance(payload, list):
            raise ValueError(f"Cost file {path} must contain a JSON array")
        costs.extend(CostRecord.model_validate(item) for item in payload)
    fingerprint = hashlib.sha256(json.dumps({"system": system_name, "benchmarks": [item.run_id for item in benchmarks], "humans": [item.evaluation_id for item in humans], "baselines": [item.comparison_id for item in baselines], "ablations": [item.ablation_id for item in ablations], "costs": [item.run_id for item in costs]}, sort_keys=True).encode("utf-8")).hexdigest()[:20]
    return EvaluationReport(report_id=f"report:{fingerprint}", system_name=system_name, benchmark_results=benchmarks, human_evaluations=humans, baseline_comparisons=baselines, ablations=ablations, costs=costs)
