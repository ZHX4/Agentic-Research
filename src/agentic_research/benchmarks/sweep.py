"""Report-only threshold sensitivity harness.

sensitivity analysis != calibration.
benchmark-specific optimization is prohibited.

The harness varies configurations and reports outcome deltas. It never
selects a best configuration and never writes back into Phase 4/5/6
defaults.
"""

from __future__ import annotations

import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SENSITIVITY_NOTE = (
    "sensitivity analysis != calibration; benchmark-specific optimization is prohibited."
)

SweepDimension = Literal[
    "near_match_similarity",
    "deep_verification_similarity_floor",
    "max_deep_verifications",
    "dedup_similarity_threshold",
    "clustering_threshold",
    "max_underexplored_coverage",
    "min_entity_support",
]

SWEEP_GRID: dict[str, list[float | int]] = {
    "near_match_similarity": [0.62, 0.72, 0.82],
    "deep_verification_similarity_floor": [0.35, 0.45, 0.55],
    "max_deep_verifications": [3, 5, 8],
    "dedup_similarity_threshold": [0.75, 0.82, 0.90],
    "clustering_threshold": [0.60, 0.70, 0.80],
    "max_underexplored_coverage": [0.10, 0.20, 0.30],
    "min_entity_support": [1, 2, 3],
}

BASELINE_CONFIG: dict[str, float | int] = {
    "near_match_similarity": 0.72,
    "deep_verification_similarity_floor": 0.45,
    "max_deep_verifications": 5,
    "dedup_similarity_threshold": 0.82,
    "clustering_threshold": 0.70,
    "max_underexplored_coverage": 0.20,
    "min_entity_support": 2,
}


class SweepedOutcome(BaseModel):
    """Outcome of one swept configuration (filled by the runner)."""

    model_config = ConfigDict(extra="forbid")

    config: dict[str, float | int | str | bool] = Field(default_factory=dict)
    candidate_count: int = Field(ge=0)
    supported_count: int = Field(ge=0)
    disproved_count: int = Field(ge=0)
    flips_vs_baseline: int = Field(ge=0)
    confusion_delta: dict[str, float | int] = Field(default_factory=dict)


class SweepReport(BaseModel):
    """Deterministic report over a grid of configurations."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(min_length=1)
    baseline: dict[str, float | int] = Field(default_factory=dict)
    outcomes: list[SweepedOutcome] = Field(default_factory=list)
    note: str = Field(default=SENSITIVITY_NOTE)
    report_id: str = Field(min_length=1)

    def ensure_note(self) -> None:
        if "prohibited" not in self.note:
            raise ValueError("Sweep report must carry the non-optimization banner")


def sweep_configurations(
    dimensions: list[str] | None = None,
) -> list[dict[str, float | int]]:
    """One-dimension-at-a-time sweep around BASELINE_CONFIG (deterministic)."""
    dims = dimensions or sorted(SWEEP_GRID)
    configs: list[dict[str, float | int]] = [dict(BASELINE_CONFIG)]
    for dim in dims:
        if dim not in SWEEP_GRID:
            raise ValueError(f"Unknown sweep dimension {dim!r}")
        for value in SWEEP_GRID[dim]:
            if BASELINE_CONFIG.get(dim) == value:
                continue
            candidate = dict(BASELINE_CONFIG)
            candidate[dim] = value
            configs.append(candidate)
    return configs


def sweep_report_id(benchmark_id: str, configs: list[dict[str, float | int | str | bool]]) -> str:
    payload = json.dumps(configs, sort_keys=True, separators=(",", ":"))
    return "sweep:" + hashlib.sha256((benchmark_id + "||" + payload).encode()).hexdigest()[:20]


def build_sweep_report(
    benchmark_id: str,
    outcomes: list[SweepedOutcome],
    *,
    baseline: dict[str, float | int] | None = None,
) -> SweepReport:
    base = baseline or dict(BASELINE_CONFIG)
    configs = [dict(o.config) for o in outcomes] or [dict(base)]
    return SweepReport(
        benchmark_id=benchmark_id,
        baseline=base,
        outcomes=outcomes,
        note=SENSITIVITY_NOTE,
        report_id=sweep_report_id(benchmark_id, configs),
    )
