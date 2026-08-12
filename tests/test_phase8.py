from __future__ import annotations

import hashlib

import pytest
from typer.testing import CliRunner

from agentic_research.evaluation.cli import app
from agentic_research.evaluation.comparison import compare_baselines, evaluate_ablation, summarize_costs
from agentic_research.evaluation.engine import evaluate_extraction, evaluate_labels, evaluate_retrieval, evaluate_temporal
from agentic_research.evaluation.human import evaluate_human_ratings
from agentic_research.evaluation.metrics import average_precision_at_k, bootstrap_mean_ci, cohen_kappa, macro_field_f1, ndcg_at_k, temporal_leakage
from agentic_research.evaluation.report import build_report
from agentic_research.schemas.phase8 import AblationSpec, BenchmarkCase, BenchmarkResult, CostRecord, HumanRating, PredictionRecord


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def retrieval_case(case_id: str = "c1") -> BenchmarkCase:
    return BenchmarkCase(case_id=case_id, kind="retrieval", input_hash=h(case_id), expected_ids=["a", "b"])


def test_retrieval_metrics_are_correct() -> None:
    assert average_precision_at_k(["a", "x", "b"], {"a", "b"}, 3) == pytest.approx((1.0 + 2 / 3) / 2)
    expected = (1.0 + 1 / 2.0) / (1.0 + 1 / 1.5849625007)
    assert ndcg_at_k(["a", "x", "b"], {"a", "b"}, 3) == pytest.approx(expected)


def test_mrr_rejects_mismatched_lengths() -> None:
    from agentic_research.evaluation.metrics import mean_reciprocal_rank
    with pytest.raises(ValueError):
        mean_reciprocal_rank([["a"]], [])


def test_retrieval_benchmark_runs() -> None:
    result = evaluate_retrieval([retrieval_case()], [PredictionRecord(case_id="c1", predicted_ids=["a", "b"])], system_name="test", benchmark_id="r")
    assert result.cases_evaluated == 1
    assert {metric.name for metric in result.metrics} >= {"mrr", "ndcg@10"}


def test_extraction_and_label_benchmarks() -> None:
    case = BenchmarkCase(case_id="c1", kind="extraction", input_hash=h("c1"), expected_fields={"method": "M"})
    extraction = evaluate_extraction([case], [PredictionRecord(case_id="c1", extracted_fields={"method": "M"})], system_name="test", benchmark_id="e")
    assert extraction.metrics[0].value == 1.0
    assert macro_field_f1([{"method": "M improves RAG"}], [{"method": "M improves retrieval"}]) > 0.5
    gap_case = BenchmarkCase(case_id="g1", kind="gap", input_hash=h("g1"), expected_labels=["positive"])
    labels = evaluate_labels([gap_case], [PredictionRecord(case_id="g1", predicted_labels=["positive"])], kind="gap", system_name="test", benchmark_id="g")
    assert labels.metrics[0].value == 1.0


def test_temporal_benchmark_detects_leakage_and_unknown_rate() -> None:
    case = BenchmarkCase(case_id="t1", kind="temporal", input_hash=h("t1"), cutoff_year=2020)
    prediction = PredictionRecord(case_id="t1", publication_years={"a": 2021, "b": None, "c": 2019})
    result = evaluate_temporal([case], [prediction], system_name="test", benchmark_id="t")
    metric_map = {metric.name: metric.value for metric in result.metrics}
    assert metric_map["leakage_rate"] == pytest.approx(1 / 3)
    assert metric_map["unknown_year_rate"] == pytest.approx(1 / 3)
    assert result.warnings
    assert temporal_leakage(prediction.publication_years, 2020)["leakage_rate"] == pytest.approx(1 / 3)


def test_human_agreement_requires_two_annotators() -> None:
    ratings = [HumanRating(case_id="1", annotator_id="a", label="good"), HumanRating(case_id="1", annotator_id="b", label="good")]
    result = evaluate_human_ratings(ratings, evaluation_id="h1", task="gap_quality")
    assert result.annotator_count == 2
    assert cohen_kappa(["good", "bad"], ["good", "bad"]) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        evaluate_human_ratings([HumanRating(case_id="1", annotator_id="a", label="good")], evaluation_id="h2", task="gap_quality")


def test_baseline_direction_and_ablation() -> None:
    comparison = compare_baselines("system", {"latency": 2.0}, {"b": {"latency": 3.0}}, comparison_id="cmp", metric_name="latency", direction="lower")
    assert comparison.winner == "system"
    ablation = evaluate_ablation(AblationSpec(ablation_id="a", component="retrieval", enabled=False, matched_case_ids=["1"]), {"score": 0.8}, {"score": 0.7})
    assert ablation.deltas["score"] == pytest.approx(-0.1)


def test_cost_summary() -> None:
    metrics = summarize_costs([CostRecord(run_id="r1", wall_seconds=2, cpu_seconds=3, estimated_cost_usd=0.1), CostRecord(run_id="r2", wall_seconds=4, cpu_seconds=5, estimated_cost_usd=0.2)])
    names = {metric.name for metric in metrics}
    assert "total_wall_seconds" in names
    assert "total_estimated_cost_usd" in names


def test_bootstrap_is_deterministic() -> None:
    assert bootstrap_mean_ci([1.0, 2.0, 3.0], seed=42) == bootstrap_mean_ci([1.0, 2.0, 3.0], seed=42)


def test_composite_report_is_content_addressed(tmp_path) -> None:
    benchmark = BenchmarkResult(run_id="eval:1", benchmark_id="r", kind="retrieval", system_name="test", split="test", metrics=[], cases_evaluated=1)
    benchmark_path = tmp_path / "benchmark.json"
    benchmark_path.write_text(benchmark.model_dump_json(), encoding="utf-8")
    first = build_report("test", benchmark_files=[benchmark_path])
    second = build_report("test", benchmark_files=[benchmark_path])
    assert first.report_id == second.report_id


def test_cli_surface() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "retrieval" in result.stdout
    assert "temporal" in result.stdout
    assert "report" in result.stdout
