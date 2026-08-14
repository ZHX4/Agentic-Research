from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from .controller import AutonomousController, AutonomousRunConfig, _build_controller, build_autonomous_report, load_callable_adapters, _identity, StageAdapter

app = typer.Typer(help="Phase 9 autonomous research CLI.")


def _adapters(adapters_file: Path | None, offline_smoke_test: bool) -> list[StageAdapter]:
    if offline_smoke_test:
        return [StageAdapter(name, _identity(name)) for name in ("gap", "verify", "hypothesis", "execute", "evaluate", "report")]
    if adapters_file is None:
        raise typer.BadParameter("--adapters-file is required unless --offline-smoke-test is explicitly enabled")
    return load_callable_adapters(adapters_file)


def _resume_payload(controller: AutonomousController, run_id: str) -> dict[str, Any]:
    state = controller.resume(run_id)
    successful = [item for item in state.stage_executions if item.iteration == state.iteration and item.status == "succeeded" and item.output_artifact]
    if not successful:
        return {}
    order = {stage: index for index, stage in enumerate(controller.ORDER)}
    execution = max(successful, key=lambda item: order[item.stage])
    artifact = Path(execution.output_artifact or "")
    if not artifact.is_file() or not execution.output_sha256:
        raise typer.BadParameter(f"Cannot resume: missing artifact for {execution.stage}")
    contents = artifact.read_text(encoding="utf-8")
    from .controller import _sha256
    if _sha256(contents) != execution.output_sha256:
        raise typer.BadParameter(f"Cannot resume: artifact hash mismatch for {artifact}")
    payload = json.loads(contents)
    if not isinstance(payload, dict):
        raise typer.BadParameter("Cannot resume: last stage artifact is not a JSON object")
    return payload


@app.command()
def run(
    run_id: str = typer.Option(...),
    state_db: Path = typer.Option(Path("artifacts/autonomy.sqlite")),
    input_file: Path = typer.Option(..., exists=True, readable=True),
    output: Path = typer.Option(...),
    adapters_file: Path | None = typer.Option(None),
    max_iterations: int = typer.Option(3, min=1, max=100),
    offline_smoke_test: bool = typer.Option(False),
) -> None:
    adapters = _adapters(adapters_file, offline_smoke_test)
    controller = _build_controller(state_db, adapters)
    if controller.store.load(run_id) is None:
        controller.create(run_id, AutonomousRunConfig(max_iterations=max_iterations))
    payload = json.loads(input_file.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise typer.BadParameter("Input file must contain a JSON object")
    state = controller.run(run_id, payload)
    report = build_autonomous_report(state)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(f"Wrote autonomous report {report.report_id} to {output}")


@app.command()
def resume(
    run_id: str = typer.Option(...),
    state_db: Path = typer.Option(Path("artifacts/autonomy.sqlite")),
    output: Path = typer.Option(...),
    adapters_file: Path | None = typer.Option(None),
    offline_smoke_test: bool = typer.Option(False),
) -> None:
    adapters = _adapters(adapters_file, offline_smoke_test)
    controller = _build_controller(state_db, adapters)
    payload = _resume_payload(controller, run_id)
    state = controller.run(run_id, payload)
    report = build_autonomous_report(state)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(f"Resumed autonomous run {run_id}; wrote report {report.report_id} to {output}")


if __name__ == "__main__":
    app()
