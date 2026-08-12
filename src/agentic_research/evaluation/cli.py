"""CLI for Phase 8 evaluation and benchmarking."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, TypeVar

import typer
from pydantic import BaseModel

from agentic_research.evaluation.comparison import compare_baselines, evaluate_ablation, summarize_costs
from agentic_research.evaluation.engine import evaluate_extraction, evaluate_labels, evaluate_retrieval, evaluate_temporal
from agentic_research.evaluation.human import evaluate_human_ratings
from agentic_research.schemas.phase8 import AblationSpec, BenchmarkCase, CostRecord, HumanRating, PredictionRecord

app = typer.Typer(help="Agentic-Research Phase 8 evaluation and benchmarking.")
T = TypeVar("T", bound=BaseModel)


def _read_json_list(path: Path, model: type[T]) -> list[T]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise typer.BadParameter(f"{path} must contain a JSON array")
    return [model.model_validate(item) for item in payload]


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


@app.command()
def retrieval(cases: Path = typer.Option(..., exists=True, readable=True), predictions: Path = typer.Option(..., exists=True, readable=True), output: Path = typer.Option(...), system_name: str = typer.Option(...), benchmark_id: str = typer.Option("retrieval"), split: Literal["dev", "test"] = typer.Option("test"), k: int = typer.Option(10, min=1, max=1000)) -> None:
    result = evaluate_retrieval(_read_json_list(cases, BenchmarkCase), _read_json_list(predictions, PredictionRecord), system_name=system_name, benchmark_id=benchmark_id, split=split, k=k)
    _write(output, result.model_dump(mode="json"))


@app.command()
def extraction(cases: Path = typer.Option(..., exists=True, readable=True), predictions: Path = typer.Option(..., exists=True, readable=True), output: Path = typer.Option(...), system_name: str = typer.Option(...)) -> None:
    result = evaluate_extraction(_read_json_list(cases, BenchmarkCase), _read_json_list(predictions, PredictionRecord), system_name=system_name, benchmark_id="extraction")
    _write(output, result.model_dump(mode="json"))


@app.command(name="classification")
def classification(cases: Path = typer.Option(..., exists=True, readable=True), predictions: Path = typer.Option(..., exists=True, readable=True), output: Path = typer.Option(...), system_name: str = typer.Option(...), kind: Literal["gap", "novelty"] = typer.Option("gap"), positive: str | None = typer.Option(None)) -> None:
    result = evaluate_labels(_read_json_list(cases, BenchmarkCase), _read_json_list(predictions, PredictionRecord), kind=kind, system_name=system_name, benchmark_id=kind, positive=positive)
    _write(output, result.model_dump(mode="json"))


@app.command()
def temporal(cases: Path = typer.Option(..., exists=True, readable=True), predictions: Path = typer.Option(..., exists=True, readable=True), output: Path = typer.Option(...), system_name: str = typer.Option(...)) -> None:
    result = evaluate_temporal(_read_json_list(cases, BenchmarkCase), _read_json_list(predictions, PredictionRecord), system_name=system_name, benchmark_id="temporal")
    _write(output, result.model_dump(mode="json"))


@app.command()
def human(ratings: Path = typer.Option(..., exists=True, readable=True), output: Path = typer.Option(...), evaluation_id: str = typer.Option(...), task: Literal["gap_quality", "novelty_verdict", "extraction_quality", "hypothesis_quality"] = typer.Option(...)) -> None:
    result = evaluate_human_ratings(_read_json_list(ratings, HumanRating), evaluation_id=evaluation_id, task=task)
    _write(output, result.model_dump(mode="json"))


@app.command()
def baseline(primary: Path = typer.Option(..., exists=True, readable=True), baselines: Path = typer.Option(..., exists=True, readable=True), output: Path = typer.Option(...), primary_name: str = typer.Option(...), comparison_id: str = typer.Option(...), metric_name: str | None = typer.Option(None), direction: Literal["higher", "lower"] = typer.Option("higher")) -> None:
    primary_payload = json.loads(primary.read_text(encoding="utf-8")); baseline_payload = json.loads(baselines.read_text(encoding="utf-8"))
    result = compare_baselines(primary_name, {str(k): float(v) for k, v in primary_payload.items()}, {str(name): {str(k): float(v) for k, v in values.items()} for name, values in baseline_payload.items()}, comparison_id=comparison_id, metric_name=metric_name, direction=direction)
    _write(output, result.model_dump(mode="json"))


@app.command()
def ablation(spec: Path = typer.Option(..., exists=True, readable=True), baseline_metrics: Path = typer.Option(..., exists=True, readable=True), ablated_metrics: Path = typer.Option(..., exists=True, readable=True), output: Path = typer.Option(...)) -> None:
    result = evaluate_ablation(AblationSpec.model_validate_json(spec.read_text(encoding="utf-8")), {str(k): float(v) for k, v in json.loads(baseline_metrics.read_text(encoding="utf-8")).items()}, {str(k): float(v) for k, v in json.loads(ablated_metrics.read_text(encoding="utf-8")).items()})
    _write(output, result.model_dump(mode="json"))


@app.command(name="summarize-cost")
def summarize_cost(costs: Path = typer.Option(..., exists=True, readable=True), output: Path = typer.Option(...)) -> None:
    _write(output, [metric.model_dump(mode="json") for metric in summarize_costs(_read_json_list(costs, CostRecord))])


if __name__ == "__main__":
    app()
