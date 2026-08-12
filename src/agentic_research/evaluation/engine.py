"""Benchmark orchestration with explicit temporal and provenance safeguards."""
from __future__ import annotations

import hashlib
import json
from statistics import mean

from agentic_research.schemas.phase8 import BenchmarkCase, BenchmarkResult, CostRecord, MetricValue, PredictionRecord

from .metrics import average_precision_at_k, binary_classification_metrics, bootstrap_mean_ci, macro_field_f1, mean_reciprocal_rank, ndcg_at_k, precision_recall_f1, temporal_leakage


def stable_run_id(*parts: str) -> str:
    return "eval:" + hashlib.sha256("||".join(parts).encode("utf-8")).hexdigest()[:20]


def evaluate_retrieval(cases: list[BenchmarkCase], predictions: list[PredictionRecord], *, system_name: str, benchmark_id: str, split: str = "test", k: int = 10) -> BenchmarkResult:
    by_id = {p.case_id: p for p in predictions}
    ranked: list[list[str]] = []
    gold: list[set[str]] = []
    aps: list[float] = []
    ndcgs: list[float] = []
    for case in cases:
        prediction = by_id.get(case.case_id, PredictionRecord(case_id=case.case_id))
        ranked.append(prediction.predicted_ids)
        gold.append(set(case.expected_ids))
        aps.append(average_precision_at_k(prediction.predicted_ids, set(case.expected_ids), k))
        ndcgs.append(ndcg_at_k(prediction.predicted_ids, set(case.expected_ids), k))
    mrr = mean_reciprocal_rank(ranked, gold)
    precisions: list[float] = []
    recalls: list[float] = []
    f1s: list[float] = []
    for got, expected in zip(ranked, gold):
        p, r, f = precision_recall_f1(got[:k], expected)
        precisions.append(p); recalls.append(r); f1s.append(f)
    return BenchmarkResult(
        run_id=stable_run_id(benchmark_id, system_name, split, json.dumps([c.case_id for c in cases], sort_keys=True)),
        benchmark_id=benchmark_id, kind="retrieval", system_name=system_name, split=split,
        cases_evaluated=len(cases), metrics=[
            MetricValue(name=f"precision@{k}", value=mean(precisions) if precisions else 0.0, n=len(cases)),
            MetricValue(name=f"recall@{k}", value=mean(recalls) if recalls else 0.0, n=len(cases)),
            MetricValue(name=f"f1@{k}", value=mean(f1s) if f1s else 0.0, n=len(cases)),
            MetricValue(name="mrr", value=mrr, n=len(cases)),
            MetricValue(name=f"map@{k}", value=mean(aps) if aps else 0.0, n=len(cases)),
            MetricValue(name=f"ndcg@{k}", value=mean(ndcgs) if ndcgs else 0.0, n=len(cases)),
        ],
    )


def evaluate_extraction(cases: list[BenchmarkCase], predictions: list[PredictionRecord], *, system_name: str, benchmark_id: str, split: str = "test") -> BenchmarkResult:
    by_id = {p.case_id: p for p in predictions}
    expected = [case.expected_fields for case in cases]
    predicted = [by_id.get(case.case_id, PredictionRecord(case_id=case.case_id)).extracted_fields for case in cases]
    exact = sum(1.0 if p == e else 0.0 for p, e in zip(predicted, expected)) / len(cases) if cases else 0.0
    macro_f1 = macro_field_f1(predicted, expected)
    return BenchmarkResult(
        run_id=stable_run_id(benchmark_id, system_name, split), benchmark_id=benchmark_id, kind="extraction", system_name=system_name, split=split,
        cases_evaluated=len(cases), metrics=[MetricValue(name="exact_match", value=exact, n=len(cases)), MetricValue(name="macro_field_f1", value=macro_f1, n=len(cases))],
    )


def evaluate_labels(cases: list[BenchmarkCase], predictions: list[PredictionRecord], *, kind: str, system_name: str, benchmark_id: str, positive: str | None = None, split: str = "test") -> BenchmarkResult:
    if kind not in {"gap", "novelty"}:
        raise ValueError("kind must be gap or novelty")
    by_id = {p.case_id: p for p in predictions}
    expected = [case.expected_labels[0] if case.expected_labels else "" for case in cases]
    predicted = [by_id.get(case.case_id, PredictionRecord(case_id=case.case_id)).predicted_labels[0] if by_id.get(case.case_id) and by_id[case.case_id].predicted_labels else "" for case in cases]
    labels = binary_classification_metrics(predicted, expected, positive=positive or (expected[0] if expected else "")) if cases and positive else None
    metrics = []
    if labels:
        metrics = [MetricValue(name=name, value=value, n=len(cases)) for name, value in labels.items()]
    else:
        exact = mean(1.0 if p == e else 0.0 for p, e in zip(predicted, expected)) if cases else 0.0
        metrics = [MetricValue(name="accuracy", value=exact, n=len(cases))]
    return BenchmarkResult(run_id=stable_run_id(benchmark_id, system_name, split, kind), benchmark_id=benchmark_id, kind=kind, system_name=system_name, split=split, cases_evaluated=len(cases), metrics=metrics)


def evaluate_temporal(cases: list[BenchmarkCase], predictions: list[PredictionRecord], *, system_name: str, benchmark_id: str) -> BenchmarkResult:
    if not cases or any(case.cutoff_year is None for case in cases):
        raise ValueError("Every temporal case requires a cutoff_year")
    by_id = {p.case_id: p for p in predictions}
    leakage_values: list[float] = []
    unknown_values: list[float] = []
    warnings: list[str] = []
    for case in cases:
        prediction = by_id.get(case.case_id, PredictionRecord(case_id=case.case_id))
        stats = temporal_leakage(prediction.publication_years, case.cutoff_year or 0)
        leakage_values.append(stats["leakage_rate"]); unknown_values.append(stats["unknown_year_items"])
        if stats["leakage_rate"] > 0:
            warnings.append(f"Temporal leakage detected in {case.case_id}")
    return BenchmarkResult(
        run_id=stable_run_id(benchmark_id, system_name, "temporal_test"), benchmark_id=benchmark_id, kind="temporal", system_name=system_name, split="temporal_test", cases_evaluated=len(cases),
        metrics=[MetricValue(name="leakage_rate", value=mean(leakage_values), direction="lower", n=len(cases)), MetricValue(name="unknown_year_rate", value=mean(unknown_values), direction="lower", n=len(cases))], warnings=warnings,
    )


def summarize_cost(costs: list[CostRecord]) -> list[MetricValue]:
    if not costs:
        return []
    def avg(field: str) -> float | None:
        values = [getattr(item, field) for item in costs if getattr(item, field) is not None]
        return mean(values) if values else None
    metrics: list[MetricValue] = [MetricValue(name="mean_wall_seconds", value=mean(c.wall_seconds for c in costs), unit="seconds", n=len(costs))]
    for field in ("cpu_seconds", "gpu_seconds", "peak_memory_mb", "input_tokens", "output_tokens", "estimated_cost_usd"):
        value = avg(field)
        if value is not None:
            metrics.append(MetricValue(name=f"mean_{field}", value=value, n=len(costs)))
    return metrics


def temporal_bootstrap(values: list[float], *, seed: int = 0) -> MetricValue:
    lo, hi = bootstrap_mean_ci(values, seed=seed)
    return MetricValue(name="mean_with_bootstrap_ci", value=mean(values) if values else 0.0, details={"ci_low": lo, "ci_high": hi, "n": len(values)})
