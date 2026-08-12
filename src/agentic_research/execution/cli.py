"""CLI for Phase 7 scientific planning and execution."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import typer

from agentic_research.execution.planner import build_experiment_spec
from agentic_research.execution.runner import run_experiment
from agentic_research.execution.tree import append_result, create_tree
from agentic_research.schemas.phase6 import HypothesisRun
from agentic_research.schemas.phase7 import DatasetManifest, ExperimentResult, ExperimentSearchTree, ExperimentSpec

app = typer.Typer(help="Agentic-Research Phase 7 scientific execution.")


@app.command(name="plan")
def plan(
    hypothesis_run: Path = typer.Option(..., exists=True, readable=True),
    hypothesis_id: str = typer.Option(...),
    code: Path = typer.Option(..., exists=True, readable=True),
    command: list[str] = typer.Option(..., help="Executable argv; repeat the option for each token."),
    dataset_manifest: list[Path] = typer.Option([], exists=True, readable=True),
    primary_metric: str = typer.Option(...),
    metric_direction: Literal["higher", "lower"] = typer.Option("higher"),
    output: Path = typer.Option(...),
    seeds: list[int] = typer.Option([1, 2, 3]),
    image: str = typer.Option("python:3.11-slim"),
    network: bool = typer.Option(False),
    gpu: bool = typer.Option(False),
    timeout: int = typer.Option(3600, min=1, max=86400),
) -> None:
    """Create a reproducible ExperimentSpec from a Phase 6 hypothesis."""
    run = HypothesisRun.model_validate_json(hypothesis_run.read_text(encoding="utf-8"))
    selected = next((item.hypothesis for item in run.candidates if item.hypothesis.hypothesis_id == hypothesis_id), None)
    if selected is None:
        raise typer.BadParameter(f"Unknown hypothesis_id: {hypothesis_id}")
    datasets = [DatasetManifest.model_validate_json(path.read_text(encoding="utf-8")) for path in dataset_manifest]
    spec = build_experiment_spec(
        selected,
        code_path=code,
        command=command,
        datasets=datasets,
        primary_metric=primary_metric,
        metric_direction=metric_direction,
        seeds=seeds,
        image=image,
        network_enabled=network,
        allow_gpu=gpu,
        timeout_seconds=timeout,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(spec.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(f"Wrote experiment plan {spec.experiment_id} to {output}")


@app.command(name="execute")
def execute(
    spec: Path = typer.Option(..., exists=True, readable=True),
    code_dir: Path = typer.Option(..., exists=True, readable=True),
    output_dir: Path = typer.Option(...),
    result: Path = typer.Option(...),
) -> None:
    """Execute a planned experiment inside the configured Docker sandbox."""
    experiment = ExperimentSpec.model_validate_json(spec.read_text(encoding="utf-8"))
    execution_result = run_experiment(experiment, code_dir=code_dir, output_dir=output_dir)
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text(execution_result.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(f"Wrote execution result {execution_result.result_id} to {result}")


@app.command(name="tree")
def tree(
    spec: Path = typer.Option(..., exists=True, readable=True),
    output: Path = typer.Option(...),
    base_tree: Path | None = typer.Option(None, exists=True, readable=True, help="Existing ExperimentSearchTree JSON to extend."),
    result: Path | None = typer.Option(None, exists=True, readable=True),
    relation: Literal["mutation", "ablation", "replication", "branch"] = typer.Option("replication"),
) -> None:
    """Create or extend an experiment search tree."""
    experiment = ExperimentSpec.model_validate_json(spec.read_text(encoding="utf-8"))
    tree_obj = ExperimentSearchTree.model_validate_json(base_tree.read_text(encoding="utf-8")) if base_tree is not None else create_tree(experiment)
    if result is not None:
        execution_result = ExperimentResult.model_validate_json(result.read_text(encoding="utf-8"))
        tree_obj = append_result(tree_obj, execution_result, relation=relation)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(tree_obj.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(f"Wrote experiment tree to {output}")


if __name__ == "__main__":
    app()
