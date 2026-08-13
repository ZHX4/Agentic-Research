"""Closed-loop orchestration over the existing Phase 4-8 stage implementations."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal

from agentic_research.schemas.phase9 import AutonomousRunConfig, AutonomousRunState, Checkpoint, StageExecution

from .state_store import SQLiteRunStore

StageName = Literal["gap", "verify", "hypothesis", "execute", "evaluate", "review", "report"]
StageCallable = Callable[[dict[str, Any]], dict[str, Any]]


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


class AutonomousController:
    """Deterministic controller with atomic checkpointing, bounded retries, and resume."""

    ORDER: tuple[StageName, ...] = ("gap", "verify", "hypothesis", "execute", "evaluate", "review", "report")

    def __init__(self, store: SQLiteRunStore, adapters: list[StageAdapter], *, reviewers: Any | None = None) -> None:
        self.store = store
        self.adapters = {adapter.name: adapter for adapter in adapters}
        self.reviewers = reviewers
        missing = [stage for stage in self.ORDER if stage not in self.adapters and stage != "review"]
        if missing:
            raise ValueError(f"Missing stage adapters: {missing}")
        if reviewers is None:
            raise ValueError("A reviewer panel is required for Phase 9")

    def create(self, run_id: str, config: AutonomousRunConfig) -> AutonomousRunState:
        state = AutonomousRunState(run_id=run_id, status="planned", iteration=0, config=config)
        self._persist(state)
        return state

    def resume(self, run_id: str) -> AutonomousRunState:
        loaded = self.store.load(run_id)
        if loaded is None:
            raise KeyError(f"Unknown run_id: {run_id}")
        state, stored_sha = loaded
        actual_sha = _sha256(state.model_dump_json())
        if actual_sha != stored_sha:
            raise ValueError("Persisted state hash mismatch; refusing to resume")
        return state

    def run(self, run_id: str, initial_payload: dict[str, Any]) -> AutonomousRunState:
        state = self.resume(run_id)
        if state.status in {"completed", "cancelled"}:
            return state
        state.status = "running"
        payload = initial_payload
        while state.iteration < state.config.max_iterations:
            progressed = False
            for stage in self.ORDER:
                if stage == "review":
                    review_target = payload.get("review_target") or payload
                    review_round = self.reviewers.review(state.iteration, str(review_target.get("kind", "run")), str(review_target.get("id", state.run_id)), review_target)
                    state.reviews.append(review_round)
                    state.current_stage = "review"
                    state.provenance_refs.extend(review_round.findings[0].evidence_refs if review_round.findings else [])
                    self._checkpoint(state, "review")
                    if review_round.consensus == "reject" and state.config.stop_on_critical_review:
                        state.status = "failed"
                        state.stop_reason = "Critical/negative reviewer decision"
                        state.current_stage = None
                        self._persist(state)
                        return state
                    if review_round.consensus == "revise":
                        payload = {**payload, "review": review_round.model_dump(mode="json")}
                        progressed = True
                    continue
                adapter = self.adapters[stage]
                stage_id = f"stage:{state.iteration}:{stage}"
                previous = next((item for item in state.stage_executions if item.stage_id == stage_id), None)
                if previous is not None and previous.status == "succeeded":
                    payload = json.loads(Path(previous.output_artifact).read_text(encoding="utf-8")) if previous.output_artifact else payload
                    continue
                execution = StageExecution(stage_id=stage_id, iteration=state.iteration, stage=stage, status="running", attempts=1)
                state.stage_executions.append(execution)
                state.current_stage = stage
                self._persist(state)
                try:
                    input_sha = _sha256(_canonical(payload))
                    result = adapter.runner(payload)
                    if not isinstance(result, dict):
                        raise TypeError(f"Stage {stage} must return a JSON object")
                    artifact_path = self._write_artifact(run_id, state.iteration, stage, result)
                    output_sha = _sha256(Path(artifact_path).read_text(encoding="utf-8"))
                    execution.status = "succeeded"
                    execution.input_sha256 = input_sha
                    execution.output_artifact = str(artifact_path)
                    execution.output_sha256 = output_sha
                    payload = result
                    progressed = True
                except Exception as exc:  # noqa: BLE001
                    execution.status = "failed"
                    execution.error = str(exc)
                    if execution.attempts >= state.config.max_stage_retries + 1:
                        state.status = "failed"
                        state.stop_reason = f"Stage {stage} failed: {exc}"
                        state.current_stage = None
                        self._persist(state)
                        return state
                self._checkpoint(state, stage)
            signature = _sha256(_canonical({"iteration": state.iteration, "payload": payload, "reviews": [review.model_dump(mode="json") for review in state.reviews[-2:]]}))
            if signature in state.progress_signatures:
                if state.config.stop_on_no_progress:
                    state.status = "completed"
                    state.stop_reason = "No progress detected"
                    state.current_stage = None
                    self._persist(state)
                    return state
            state.progress_signatures.append(signature)
            state.iteration += 1
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

    def _write_artifact(self, run_id: str, iteration: int, stage: str, payload: dict[str, Any]) -> Path:
        root = self.store.path.parent / "phase9" / run_id
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"iteration-{iteration:03d}-{stage}.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
        return path

    def _persist(self, state: AutonomousRunState) -> None:
        state_json = state.model_dump_json()
        self.store.save(state, _sha256(state_json))

    def _checkpoint(self, state: AutonomousRunState, stage: StageName) -> None:
        if not state.config.checkpoint_every_stage:
            return
        state_json = state.model_dump_json()
        state_sha = _sha256(state_json)
        checkpoint = Checkpoint(
            checkpoint_id=f"checkpoint:{state.run_id}:{state.iteration}:{stage}",
            run_id=state.run_id,
            iteration=state.iteration,
            last_completed_stage=stage,
            state_sha256=state_sha,
            created_at=_now(),
        )
        state.checkpoints.append(checkpoint)
        self.store.save_checkpoint(checkpoint, state, state_sha)
