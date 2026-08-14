"""Phase 9 autonomous discovery control plane."""
from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal

import typer

from agentic_research.schemas.phase9 import (
    AutonomousRunConfig,
    AutonomousRunReport,
    AutonomousRunState,
    Checkpoint,
    StageExecution,
)

from .reviewers import ProvenanceReviewer, ReviewPanel, ScientificIntegrityReviewer
from .state_store import SQLiteRunStore

StageName = Literal["gap", "verify", "hypothesis", "execute", "evaluate", "review", "report"]
StageCallable = Callable[[dict[str, Any]], dict[str, Any]]

app = typer.Typer(help="Phase 9 autonomous research control plane.")


@dataclass(frozen=True)
class StageAdapter:
    name: StageName
    runner: StageCallable


def _sha256(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _checkpoint_hash(state: AutonomousRunState) -> str:
    if not state.checkpoints:
        return _sha256(state.model_dump_json())
    last = state.checkpoints[-1]
    normalized = last.model_copy(update={"state_sha256": "0" * 64})
    clone = state.model_copy(update={"checkpoints": [*state.checkpoints[:-1], normalized]})
    return _sha256(clone.model_dump_json())


def build_autonomous_report(state: AutonomousRunState) -> AutonomousRunReport:
    critical = sum(review.critical_count for review in state.reviews)
    artifacts = [item.output_artifact for item in state.stage_executions if item.output_artifact]
    payload = {
        "run_id": state.run_id,
        "status": state.status,
        "iteration": state.iteration,
        "stages": [item.model_dump(mode="json") for item in state.stage_executions],
        "reviews": [item.model_dump(mode="json") for item in state.reviews],
        "provenance": state.provenance_refs,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:24]
    warnings = list(state.warnings)
    if not state.provenance_refs:
        warnings.append("Run has no provenance references")
    return AutonomousRunReport(
        report_id=f"autonomous-report:{digest}",
        run_id=state.run_id,
        final_status=state.status,
        iterations_completed=state.iteration,
        stage_count=len(state.stage_executions),
        review_count=len(state.reviews),
        critical_findings=critical,
        provenance_refs=sorted(set(state.provenance_refs)),
        output_artifacts=artifacts,
        warnings=warnings,
        stop_reason=state.stop_reason,
    )


class AutonomousController:
    """Resumable, bounded autonomous loop with atomic state/checkpoints."""

    ORDER: tuple[StageName, ...] = ("gap", "verify", "hypothesis", "execute", "evaluate", "review", "report")
    REVIEW_STAGE_TARGETS: tuple[tuple[StageName, str], ...] = (
        ("gap", "gap"),
        ("verify", "verification"),
        ("hypothesis", "hypothesis"),
        ("execute", "execution"),
        ("evaluate", "evaluation"),
    )
    REVIEW_ID_FIELDS: dict[str, str] = {
        "gap": "gap_ids",
        "verification": "verification_ids",
        "hypothesis": "hypothesis_ids",
        "execution": "experiment_ids",
        "evaluation": "evaluation_ids",
    }

    def __init__(self, store: SQLiteRunStore, adapters: list[StageAdapter], *, reviewers: ReviewPanel) -> None:
        self.store = store
        self.adapters = {adapter.name: adapter for adapter in adapters}
        self.reviewers = reviewers
        missing = [stage for stage in self.ORDER if stage not in self.adapters and stage != "review"]
        if missing:
            raise ValueError(f"Missing stage adapters: {missing}")

    def create(self, run_id: str, config: AutonomousRunConfig) -> AutonomousRunState:
        if self.store.load(run_id) is not None:
            raise ValueError(f"Run already exists: {run_id}")
        state = AutonomousRunState(run_id=run_id, status="planned", iteration=0, config=config)
        self._persist(state)
        return state

    def resume(self, run_id: str) -> AutonomousRunState:
        loaded = self.store.load(run_id)
        if loaded is None:
            raise KeyError(f"Unknown run_id: {run_id}")
        state, stored_sha = loaded
        if _sha256(state.model_dump_json()) != stored_sha:
            raise ValueError("Persisted state hash mismatch; refusing to resume")
        return state

    @staticmethod
    def _harvest(state: AutonomousRunState, payload: dict[str, Any]) -> None:
        for field, target in (
            ("gap_ids", state.gap_ids),
            ("verification_ids", state.verification_ids),
            ("hypothesis_ids", state.hypothesis_ids),
            ("experiment_ids", state.experiment_ids),
            ("evaluation_ids", state.evaluation_ids),
            ("provenance_refs", state.provenance_refs),
        ):
            values = payload.get(field, [])
            if isinstance(values, list):
                target.extend(str(value) for value in values)
        for target in (
            state.gap_ids,
            state.verification_ids,
            state.hypothesis_ids,
            state.experiment_ids,
            state.evaluation_ids,
            state.provenance_refs,
        ):
            target[:] = sorted(set(target))

    def _stage_execution(self, state: AutonomousRunState, stage: StageName) -> StageExecution | None:
        return next(
            (
                item
                for item in reversed(state.stage_executions)
                if item.iteration == state.iteration and item.stage == stage and item.status == "succeeded"
            ),
            None,
        )

    def _load_stage_artifact(self, execution: StageExecution) -> dict[str, Any]:
        if not execution.output_artifact or not execution.output_sha256:
            raise ValueError(f"Stage {execution.stage} has no complete output artifact")
        artifact = Path(execution.output_artifact)
        if not artifact.is_file():
            raise ValueError(f"Stage artifact does not exist: {artifact}")
        contents = artifact.read_text(encoding="utf-8")
        if _sha256(contents) != execution.output_sha256:
            raise ValueError(f"Stage artifact hash mismatch: {artifact}")
        payload = json.loads(contents)
        if not isinstance(payload, dict):
            raise TypeError(f"Stage artifact must contain a JSON object: {artifact}")
        return payload

    def _run_stage_reviews(self, state: AutonomousRunState) -> list[Any]:
        rounds: list[Any] = []
        for stage, target_kind in self.REVIEW_STAGE_TARGETS:
            execution = self._stage_execution(state, stage)
            if execution is None:
                raise ValueError(f"Required stage-specific review target missing: {stage}")
            artifact = self._load_stage_artifact(execution)
            id_field = self.REVIEW_ID_FIELDS[target_kind]
            artifact_ids = artifact.get(id_field)
            if not isinstance(artifact_ids, list) or not artifact_ids:
                raise ValueError(f"Stage {stage} artifact must contain non-empty {id_field}")
            target_ids = sorted({str(item) for item in artifact_ids})
            review_artifact = dict(artifact)
            review_artifact["output_sha256"] = execution.output_sha256
            review_artifact["stage"] = stage
            review_artifact["stage_id"] = execution.stage_id
            review_artifact["input_sha256"] = execution.input_sha256
            review_artifact["provenance_refs"] = sorted(
                set([*review_artifact.get("provenance_refs", []), *state.provenance_refs])
            )
            canonical_target = _canonical({"ids": target_ids})
            target_id = target_ids[0] if len(target_ids) == 1 else f"{stage}:{_sha256(canonical_target)[:16]}"
            review_round = self.reviewers.review(state.iteration, target_kind, target_id, review_artifact)
            rounds.append(review_round)
            state.provenance_refs.extend(
                ref for finding in review_round.findings for ref in finding.evidence_refs
            )
        return rounds

    def run(self, run_id: str, initial_payload: dict[str, Any]) -> AutonomousRunState:
        state = self.resume(run_id)
        if state.status in {"completed", "cancelled"}:
            return state
        state.status = "running"
        self._harvest(state, initial_payload)
        self._persist(state)
        payload = initial_payload
        while state.iteration < state.config.max_iterations:
            progressed = False
            for stage in self.ORDER:
                if stage == "review":
                    review_rounds = self._run_stage_reviews(state)
                    state.reviews.extend(review_rounds)
                    state.current_stage = "review"
                    self._checkpoint(state, "review")
                    critical = [round_ for round_ in review_rounds if round_.critical_count > 0]
                    if critical and state.config.stop_on_critical_review:
                        state.status = "failed"
                        state.stop_reason = f"Critical reviewer finding(s): {len(critical)}"
                        state.current_stage = None
                        self._persist(state)
                        return state
                    revisions = [round_ for round_ in review_rounds if round_.consensus == "revise"]
                    if revisions:
                        payload = {**payload, "reviews": [round_.model_dump(mode="json") for round_ in review_rounds]}
                        progressed = True
                    continue

                adapter = self.adapters[stage]
                stage_id = f"stage:{state.iteration}:{stage}"
                previous = next((item for item in state.stage_executions if item.stage_id == stage_id), None)
                if previous is not None and previous.status == "succeeded" and previous.output_artifact:
                    payload = self._load_stage_artifact(previous)
                    self._harvest(state, payload)
                    continue
                execution = previous or StageExecution(
                    stage_id=stage_id,
                    iteration=state.iteration,
                    stage=stage,
                    status="running",
                    attempts=0,
                )
                if previous is None:
                    state.stage_executions.append(execution)
                execution.status = "running"
                execution.error = None
                state.current_stage = stage
                self._persist(state)
                max_attempts = state.config.max_stage_retries + 1
                while execution.attempts < max_attempts:
                    execution.attempts += 1
                    try:
                        input_sha = _sha256(_canonical(payload))
                        result = adapter.runner(payload)
                        if not isinstance(result, dict):
                            raise TypeError(f"Stage {stage} must return a JSON object")
                        artifact_path = self._write_artifact(
                            run_id, state.iteration, stage, result, execution.attempts
                        )
                        execution.input_sha256 = input_sha
                        execution.output_artifact = str(artifact_path)
                        execution.output_sha256 = _sha256(artifact_path.read_text(encoding="utf-8"))
                        execution.status = "succeeded"
                        payload = result
                        self._harvest(state, payload)
                        progressed = True
                        break
                    except Exception as exc:  # noqa: BLE001
                        execution.status = "failed"
                        execution.error = str(exc)
                        self._persist(state)
                if execution.status != "succeeded":
                    state.status = "failed"
                    state.stop_reason = (
                        f"Stage {stage} exhausted retries: {execution.error or 'unknown error'}"
                    )
                    state.current_stage = None
                    self._persist(state)
                    return state
                if stage == "evaluate" and state.config.require_phase8_evaluation and not state.evaluation_ids:
                    state.status = "failed"
                    state.stop_reason = "Required Phase 8 evaluation artifact/ID was not produced"
                    state.current_stage = None
                    self._persist(state)
                    return state
                self._checkpoint(state, stage)

            expected_review_kinds = {kind for _, kind in self.REVIEW_STAGE_TARGETS}
            actual_review_kinds = {
                finding.target_kind
                for review in state.reviews
                if review.iteration == state.iteration
                for finding in review.findings
            }
            if state.config.require_review_before_next_iteration and not expected_review_kinds.issubset(actual_review_kinds):
                state.status = "failed"
                state.stop_reason = "Iteration completed without all required stage-specific reviews"
                state.current_stage = None
                self._persist(state)
                return state
            signature = _sha256(
                _canonical(
                    {
                        "gap_ids": state.gap_ids,
                        "verification_ids": state.verification_ids,
                        "hypothesis_ids": state.hypothesis_ids,
                        "experiment_ids": state.experiment_ids,
                        "evaluation_ids": state.evaluation_ids,
                        "latest_reviews": [
                            review.model_dump(mode="json")
                            for review in state.reviews
                            if review.iteration == state.iteration
                        ],
                    }
                )
            )
            state.progress_signatures.append(signature)
            repeats = sum(1 for item in state.progress_signatures if item == signature)
            state.iteration += 1
            if repeats >= state.config.no_progress_patience and state.config.stop_on_no_progress:
                state.status = "completed"
                state.stop_reason = "No progress detected within patience budget"
                state.current_stage = None
                self._persist(state)
                return state
            if not progressed:
                state.status = "completed"
                state.stop_reason = "No stage progressed"
                state.current_stage = None
                self._persist(state)
                return state
        state.status = "completed"
        state.stop_reason = "Maximum iteration budget reached"
        state.current_stage = None
        self._persist(state)
        return state

    def _write_artifact(self, run_id: str, iteration: int, stage: str, payload: dict[str, Any], attempt: int) -> Path:
        root = self.store.path.parent / "phase9" / run_id
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"iteration-{iteration:03d}-{stage}-attempt-{attempt}.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
        return path

    def _persist(self, state: AutonomousRunState) -> None:
        self.store.save(state, _sha256(state.model_dump_json()))

    def _checkpoint(self, state: AutonomousRunState, stage: StageName) -> None:
        if not state.config.checkpoint_every_stage:
            self._persist(state)
            return
        checkpoint = Checkpoint(
            checkpoint_id=f"checkpoint:{state.run_id}:{state.iteration}:{stage}:{len(state.checkpoints)}",
            run_id=state.run_id,
            iteration=state.iteration,
            last_completed_stage=stage,
            state_sha256="0" * 64,
            created_at=_now(),
        )
        state.checkpoints.append(checkpoint)
        state.checkpoints[-1] = checkpoint.model_copy(update={"state_sha256": _checkpoint_hash(state)})
        self.store.save_checkpoint(state.checkpoints[-1], state, _sha256(state.model_dump_json()))


def _identity(name: str) -> StageCallable:
    def runner(payload: dict[str, Any]) -> dict[str, Any]:
        refs = list(payload.get("provenance_refs", []))
        refs.append(f"offline-smoke:{name}")
        result: dict[str, Any] = {
            "stage": name,
            "provenance_refs": sorted(set(refs)),
            "smoke_test": True,
        }
        digest = hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()[:16]
        if name == "gap":
            result["gap_ids"] = [f"gap:{digest}"]
        elif name == "verify":
            result["verification_ids"] = [f"verification:{digest}"]
        elif name == "hypothesis":
            result["hypothesis_ids"] = [f"hypothesis:{digest}"]
            result["falsification_condition"] = "Synthetic smoke-test threshold."
        elif name == "execute":
            result["experiment_ids"] = [f"experiment:{digest}"]
        elif name == "evaluate":
            result["evaluation_ids"] = [f"evaluation:{digest}"]
            result["cases_evaluated"] = 1
        return result
    return runner


def load_callable_adapters(manifest: Path) -> list[StageAdapter]:
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("stages"), dict):
        raise ValueError("Adapter manifest requires a stages object")
    required = {"gap", "verify", "hypothesis", "execute", "evaluate", "report"}
    missing = sorted(required - set(payload["stages"]))
    if missing:
        raise ValueError(f"Adapter manifest missing stages: {missing}")
    adapters: list[StageAdapter] = []
    for name in sorted(required):
        target = payload["stages"][name]
        if not isinstance(target, str) or ":" not in target:
            raise ValueError(f"Stage {name!r} must be a module:function reference")
        module_name, function_name = target.split(":", 1)
        function = getattr(importlib.import_module(module_name), function_name, None)
        if not callable(function):
            raise ValueError(f"Stage adapter is not callable: {target}")
        adapters.append(StageAdapter(name, function))
    return adapters


def _build_controller(state_db: Path, adapters: list[StageAdapter]) -> AutonomousController:
    store = SQLiteRunStore(state_db)
    panel = ReviewPanel([ProvenanceReviewer(), ScientificIntegrityReviewer()])
    return AutonomousController(store, adapters, reviewers=panel)


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
    if offline_smoke_test:
        adapters = [StageAdapter(name, _identity(name)) for name in ("gap", "verify", "hypothesis", "execute", "evaluate", "report")]
    elif adapters_file is None:
        raise typer.BadParameter("--adapters-file is required unless --offline-smoke-test is explicitly enabled")
    else:
        adapters = load_callable_adapters(adapters_file)
    controller = _build_controller(state_db, adapters)
    if controller.store.load(run_id) is None:
        controller.create(run_id, AutonomousRunConfig(max_iterations=max_iterations))
    payload = json.loads(input_file.read_text(encoding="utf-8"))
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
    if offline_smoke_test:
        adapters = [StageAdapter(name, _identity(name)) for name in ("gap", "verify", "hypothesis", "execute", "evaluate", "report")]
    elif adapters_file is None:
        raise typer.BadParameter("--adapters-file is required unless --offline-smoke-test is explicitly enabled")
    else:
        adapters = load_callable_adapters(adapters_file)
    controller = _build_controller(state_db, adapters)
    state = controller.resume(run_id)
    report = build_autonomous_report(state)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(f"Wrote autonomous report {report.report_id} to {output}")


if __name__ == "__main__":
    app()
