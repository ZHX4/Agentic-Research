"""Baseline, ablation, and cost comparison utilities."""
from __future__ import annotations

from statistics import mean

from agentic_research.schemas.phase8 import AblationResult, AblationSpec, BaselineComparison, BaselineSpec, CostRecord, MetricDirection, MetricValue


def compare_baselines(primary_name: str, primary_metrics: dict[str, float], baselines: dict[str, dict[str, float]], *, comparison_id: str, metric_name: str | None = None, direction: MetricDirection = "higher") -> BaselineComparison:
    if not primary_metrics:
        raise ValueError("primary_metrics cannot be empty")
    all_systems = {primary_name: primary_metrics, **baselines}
    common = sorted(set.intersection(*(set(values) for values in all_systems.values()))) if all_systems else []
    if not common:
        raise ValueError("No common metric exists across systems")
    name = metric_name or common[0]
    if name not in common:
        raise ValueError(f"Metric {name!r} is not shared by all systems")
    metrics = {system: values[name] for system, values in all_systems.items()}
    winner = (max if direction == "higher" else min)(metrics, key=metrics.get)
    deltas = {system: metrics[primary_name] - value for system, value in metrics.items() if system != primary_name}
    return BaselineComparison(comparison_id=comparison_id, metric_name=name, metric_direction=direction, primary_system=primary_name, baselines=sorted(baselines), metrics=metrics, deltas=deltas, winner=winner)


def evaluate_ablation(spec: AblationSpec, baseline_metrics: dict[str, float], ablated_metrics: dict[str, float]) -> AblationResult:
    common = sorted(set(baseline_metrics) & set(ablated_metrics))
    if not common:
        raise ValueError("No common metrics between baseline and ablation")
    deltas = {name: ablated_metrics[name] - baseline_metrics[name] for name in common}
    relative = {name: 0.0 if baseline_metrics[name] == 0 else deltas[name] / abs(baseline_metrics[name]) for name in common}
    return AblationResult(ablation_id=spec.ablation_id, component=spec.component, baseline_metrics={k: baseline_metrics[k] for k in common}, ablated_metrics={k: ablated_metrics[k] for k in common}, deltas=deltas, relative_deltas=relative)


def summarize_costs(costs: list[CostRecord]) -> list[MetricValue]:
    if not costs:
        return []
    def values(field: str) -> list[float]:
        return [float(value) for item in costs if (value := getattr(item, field)) is not None]
    metrics = [MetricValue(name="total_wall_seconds", value=sum(item.wall_seconds for item in costs), unit="seconds", n=len(costs)), MetricValue(name="mean_wall_seconds", value=mean(item.wall_seconds for item in costs), unit="seconds", n=len(costs))]
    for field, unit in (("cpu_seconds", "seconds"), ("gpu_seconds", "seconds"), ("peak_memory_mb", "MB"), ("input_tokens", "tokens"), ("output_tokens", "tokens"), ("estimated_cost_usd", "USD")):
        vals = values(field)
        if vals:
            metrics.extend([MetricValue(name=f"total_{field}", value=sum(vals), unit=unit, n=len(vals)), MetricValue(name=f"mean_{field}", value=mean(vals), unit=unit, n=len(vals))])
    return metrics


def validate_baseline(spec: BaselineSpec) -> None:
    if spec.system_type == "oracle" and not spec.notes:
        raise ValueError("Oracle baselines require an explicit note describing their information access")
