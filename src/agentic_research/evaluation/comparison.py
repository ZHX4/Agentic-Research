"""Baseline, ablation, and cost comparison utilities."""
from __future__ import annotations

from statistics import mean

from agentic_research.schemas.phase8 import AblationResult, AblationSpec, BaselineComparison, BaselineSpec, CostRecord, MetricValue


def compare_baselines(primary_name: str, primary_metrics: dict[str, float], baselines: dict[str, dict[str, float]], *, comparison_id: str) -> BaselineComparison:
    if not primary_metrics:
        raise ValueError("primary_metrics cannot be empty")
    all_systems = {primary_name: primary_metrics, **baselines}
    common_metrics = sorted(set.intersection(*(set(metrics) for metrics in all_systems.values()))) if all_systems else []
    if not common_metrics:
        raise ValueError("No common metric exists across the primary system and baselines")
    metric_name = common_metrics[0]
    metrics = {name: values[metric_name] for name, values in all_systems.items()}
    winner = max(metrics, key=metrics.get)
    deltas = {name: metrics[primary_name] - value for name, value in metrics.items() if name != primary_name}
    return BaselineComparison(
        comparison_id=comparison_id, metric_name=metric_name, primary_system=primary_name,
        baselines=sorted(baselines), metrics=metrics, deltas=deltas, winner=winner,
        warnings=[f"Winner assumes higher-is-better for {metric_name}; verify direction explicitly."],
    )


def evaluate_ablation(spec: AblationSpec, baseline_metrics: dict[str, float], ablated_metrics: dict[str, float]) -> AblationResult:
    if not baseline_metrics or not ablated_metrics:
        raise ValueError("Ablation metrics cannot be empty")
    common = sorted(set(baseline_metrics) & set(ablated_metrics))
    if not common:
        raise ValueError("No common metrics between baseline and ablation")
    deltas = {name: ablated_metrics[name] - baseline_metrics[name] for name in common}
    relative = {
        name: 0.0 if baseline_metrics[name] == 0 else deltas[name] / abs(baseline_metrics[name])
        for name in common
    }
    return AblationResult(ablation_id=spec.ablation_id, component=spec.component, baseline_metrics={k: baseline_metrics[k] for k in common}, ablated_metrics={k: ablated_metrics[k] for k in common}, deltas=deltas, relative_deltas=relative)


def summarize_costs(costs: list[CostRecord]) -> list[MetricValue]:
    if not costs:
        return []
    def values(field: str) -> list[float]:
        return [float(value) for item in costs if (value := getattr(item, field)) is not None]
    metrics = [
        MetricValue(name="total_wall_seconds", value=sum(item.wall_seconds for item in costs), unit="seconds", n=len(costs)),
        MetricValue(name="mean_wall_seconds", value=mean(item.wall_seconds for item in costs), unit="seconds", n=len(costs)),
    ]
    for field, unit in (("cpu_seconds", "seconds"), ("gpu_seconds", "seconds"), ("peak_memory_mb", "MB"), ("input_tokens", "tokens"), ("output_tokens", "tokens"), ("estimated_cost_usd", "USD")):
        vals = values(field)
        if vals:
            metrics.append(MetricValue(name=f"total_{field}", value=sum(vals), unit=unit, n=len(vals)))
            metrics.append(MetricValue(name=f"mean_{field}", value=mean(vals), unit=unit, n=len(vals)))
    return metrics


def validate_baseline(spec: BaselineSpec) -> None:
    if spec.system_type == "oracle" and not spec.notes:
        raise ValueError("Oracle baselines require an explicit note describing what information they use")
