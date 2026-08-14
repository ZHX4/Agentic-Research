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
from agentic_research.evaluation.report import build_report
from agentic_research.evaluation.validation import validate_split_disjointness
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
    _write(output, evaluate_retrieval(_read_json_list(cases, BenchmarkCase), _read_json_list(predictions, PredictionRecord), system_name=system_name, benchmark_id=benchmark_id, split=split, k=k).model_dump(mode="json"))


@app.command()
def extraction(cases: Path = typer.Option(..., exists=True, readable=True), predictions: Path = typer.Option(..., exists=True, readable=True), output: Path = typer.Option(...), system_name: str = typer.Option(...)) -> None:
    _write(output, evaluate_extraction(_read_json_list(cases, BenchmarkCase), _read_json_list(predictions, PredictionRecord), system_name=system_name, benchmark_id="extraction").model_dump(mode="json"))


@app.command(name="classification")
def classification(cases: Path = typer.Option(..., exists=True, readable=True), predictions: Path = typer.Option(..., exists=True, readable=True), output: Path = typer.Option(...), system_name: str = typer.Option(...), kind: Literal["gap", "novelty"] = typer.Option("gap"), positive: str | None = typer.Option(None)) -> None:
    _write(output, evaluate_labels(_read_json_list(cases, BenchmarkCase), _read_json_list(predictions, PredictionRecord), kind=kind, system_name=system_name, benchmark_id=kind, positive=positive).model_dump(mode="json"))


@app.command()
def temporal(cases: Path = typer.Option(..., exists=True, readable=True), predictions: Path = typer.Option(..., exists=True, readable=True), output: Path = typer.Option(...), system_name: str = typer.Option(...)) -> None:
    _write(output, evaluate_temporal(_read_json_list(cases, BenchmarkCase), _read_json_list(predictions, PredictionRecord), system_name=system_name, benchmark_id="temporal").model_dump(mode="json"))


@app.command()
def split_validate(dev: Path = typer.Option(..., exists=True, readable=True), test: Path = typer.Option(..., exists=True, readable=True), output: Path = typer.Option(...)) -> None:
    """Validate that dev/test cases are disjoint by case ID and input hash."""
    splits = {"dev": _read_json_list(dev, BenchmarkCase), "test": _read_json_list(test, BenchmarkCase)}
    validate_split_disjointness(splits)
    _write(output, {"status": "ok", "counts": {name: len(cases) for name, cases in splits.items()}})


@app.command()
def human(ratings: Path = typer.Option(..., exists=True, readable=True), output: Path = typer.Option(...), evaluation_id: str = typer.Option(...), task: Literal["gap_quality", "novelty_verdict", "extraction_quality", "hypothesis_quality"] = typer.Option(...)) -> None:
    _write(output, evaluate_human_ratings(_read_json_list(ratings, HumanRating), evaluation_id=evaluation_id, task=task).model_dump(mode="json"))


@app.command()
def baseline(primary: Path = typer.Option(..., exists=True, readable=True), baselines: Path = typer.Option(..., exists=True, readable=True), output: Path = typer.Option(...), primary_name: str = typer.Option(...), comparison_id: str = typer.Option(...), metric_name: str | None = typer.Option(None), direction: Literal["higher", "lower"] = typer.Option("higher")) -> None:
    primary_payload = json.loads(primary.read_text(encoding="utf-8"))
    baseline_payload = json.loads(baselines.read_text(encoding="utf-8"))
    result = compare_baselines(
        primary_name,
        {str(k): float(v) for k, v in primary_payload.items()},
        {str(name): {str(k): float(v) for k, v in values.items()} for name, values in baseline_payload.items()},
        comparison_id=comparison_id,
        metric_name=metric_name,
        direction=direction,
    )
    _write(output, result.model_dump(mode="json"))


@app.command()
def ablation(spec: Path = typer.Option(..., exists=True, readable=True), baseline_metrics: Path = typer.Option(..., exists=True, readable=True), ablated_metrics: Path = typer.Option(..., exists=True, readable=True), output: Path = typer.Option(...)) -> None:
    spec_obj = AblationSpec.model_validate_json(spec.read_text(encoding="utf-8"))
    baseline = {str(k): float(v) for k, v in json.loads(baseline_metrics.read_text(encoding="utf-8")).items()}
    ablated = {str(k): float(v) for k, v in json.loads(ablated_metrics.read_text(encoding="utf-8")).items()}
    _write(output, evaluate_ablation(spec_obj, baseline, ablated).model_dump(mode="json"))


@app.command(name="summarize-cost")
def summarize_cost(costs: Path = typer.Option(..., exists=True, readable=True), output: Path = typer.Option(...)) -> None:
    _write(output, [metric.model_dump(mode="json") for metric in summarize_costs(_read_json_list(costs, CostRecord))])


@app.command()
def report(system_name: str = typer.Option(...), output: Path = typer.Option(...), benchmark: list[Path] = typer.Option([], exists=True, readable=True), human: list[Path] = typer.Option([], exists=True, readable=True), baseline: list[Path] = typer.Option([], exists=True, readable=True), ablation: list[Path] = typer.Option([], exists=True, readable=True), cost: list[Path] = typer.Option([], exists=True, readable=True)) -> None:
    result = build_report(system_name, benchmark_files=benchmark, human_files=human, baseline_files=baseline, ablation_files=ablation, cost_files=cost)
    _write(output, result.model_dump(mode="json"))


if __name__ == "__main__":
    app()
