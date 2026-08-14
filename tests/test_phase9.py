from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentic_research.autonomy.controller import AutonomousController, StageAdapter, app, build_autonomous_report
from agentic_research.autonomy.reviewers import DeterministicReviewer, ReviewPanel, ScientificIntegrityReviewer
from agentic_research.autonomy.state_store import SQLiteRunStore
from agentic_research.schemas.phase9 import AutonomousRunConfig


def adapters() -> list[StageAdapter]:
    def runner(name: str):
        def run(payload: dict[str, object]) -> dict[str, object]:
            digest = str(abs(hash(name + str(sorted(payload.items())))))[:12]
            refs = list(payload.get("provenance_refs", []))
            refs.append(f"stage:{name}")
            result: dict[str, object] = {"stage": name, "provenance_refs": sorted(set(refs)), "value": name}
            if name == "gap":
                result["gap_ids"] = [f"gap:{digest}"]
            elif name == "verify":
                result["verification_ids"] = [f"verification:{digest}"]
            elif name == "hypothesis":
                result["hypothesis_ids"] = [f"hypothesis:{digest}"]
                result["falsification_condition"] = "Metric effect crosses the prespecified threshold."
            elif name == "execute":
                result["experiment_ids"] = [f"experiment:{digest}"]
            elif name == "evaluate":
                result["evaluation_ids"] = [f"evaluation:{digest}"]
                result["cases_evaluated"] = 1
            return result
        return run
    return [StageAdapter(name, runner(name)) for name in ("gap", "verify", "hypothesis", "execute", "evaluate", "report")]


def controller(tmp_path: Path, *, max_iterations: int = 1, reviewer: ReviewPanel | None = None) -> AutonomousController:
    store = SQLiteRunStore(tmp_path / "run.sqlite")
    panel = reviewer or ReviewPanel([DeterministicReviewer(), ScientificIntegrityReviewer()])
    ctl = AutonomousController(store, adapters(), reviewers=panel)
    ctl.create("run-1", AutonomousRunConfig(max_iterations=max_iterations))
    return ctl


def test_run_completes_and_persists_stage_specific_checkpoints(tmp_path: Path) -> None:
    ctl = controller(tmp_path)
    state = ctl.run("run-1", {"provenance_refs": ["input:1"]})
    assert state.status == "completed"
    assert state.checkpoints
    reviewed_kinds = {finding.target_kind for review in state.reviews for finding in review.findings}
    assert reviewed_kinds == {"gap", "verification", "hypothesis", "execution", "evaluation"}
    resumed = ctl.resume("run-1")
    assert resumed.model_dump() == state.model_dump()


def test_retry_is_bounded_and_recorded(tmp_path: Path) -> None:
    calls = {"n": 0}

    def flaky(payload: dict[str, object]) -> dict[str, object]:
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("transient")
        return {"gap_ids": ["gap:retry"], "provenance_refs": ["ok"]}

    stage_map = {adapter.name: adapter for adapter in adapters()}
    stage_map["gap"] = StageAdapter("gap", flaky)
    store = SQLiteRunStore(tmp_path / "run.sqlite")
    ctl = AutonomousController(store, list(stage_map.values()), reviewers=ReviewPanel([DeterministicReviewer()]))
    ctl.create("run-1", AutonomousRunConfig(max_iterations=1, max_stage_retries=1, require_phase8_evaluation=True))
    state = ctl.run("run-1", {"provenance_refs": ["input"]})
    assert state.status == "failed"
    gap_stage = next(item for item in state.stage_executions if item.stage == "gap")
    assert gap_stage.attempts == 2


def test_tampered_state_is_rejected(tmp_path: Path) -> None:
    ctl = controller(tmp_path)
    ctl.run("run-1", {"provenance_refs": ["input"]})
    db = SQLiteRunStore(tmp_path / "run.sqlite")
    with db._connect() as connection:
        connection.execute("UPDATE runs SET state_json='{}' WHERE run_id='run-1'")
        connection.commit()
    with pytest.raises(Exception):
        ctl.resume("run-1")


def test_reviewer_panel_is_independent_and_reports_provenance() -> None:
    panel = ReviewPanel([DeterministicReviewer(), ScientificIntegrityReviewer()])
    review = panel.review(0, "run", "run-1", {"provenance_refs": ["evidence:1"]})
    assert review.reviewer_count == 2
    assert review.consensus == "accept"
    assert review.findings[0].evidence_refs


def test_report_is_deterministic(tmp_path: Path) -> None:
    ctl = controller(tmp_path)
    state = ctl.run("run-1", {"provenance_refs": ["input"]})
    first = build_autonomous_report(state)
    second = build_autonomous_report(state)
    assert first.report_id == second.report_id
    assert first.provenance_refs


def test_cli_help() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "run" in result.stdout
    assert "resume" in result.stdout
