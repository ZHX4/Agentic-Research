from __future__ import annotations

from pathlib import Path

from agentic_research.autonomy.controller import AutonomousController, StageAdapter
from agentic_research.autonomy.reviewers import DeterministicReviewer, Reviewer, ReviewPanel
from agentic_research.autonomy.state_store import SQLiteRunStore
from agentic_research.schemas.phase9 import AutonomousRunConfig, ReviewerFinding


def _adapters() -> list[StageAdapter]:
    def make(stage: str):
        def run(payload: dict[str, object]) -> dict[str, object]:
            digest = stage
            result: dict[str, object] = {
                "provenance_refs": [f"stage:{stage}"],
                "stage": stage,
            }
            if stage == "gap":
                result["gap_ids"] = [f"gap:{digest}"]
            elif stage == "verify":
                result["verification_ids"] = [f"verification:{digest}"]
            elif stage == "hypothesis":
                result["hypothesis_ids"] = [f"hypothesis:{digest}"]
                result["falsification_condition"] = "Prespecified effect threshold is crossed."
            elif stage == "execute":
                result["experiment_ids"] = [f"experiment:{digest}"]
            elif stage == "evaluate":
                result["evaluation_ids"] = [f"evaluation:{digest}"]
                result["cases_evaluated"] = 1
            return result
        return run

    return [StageAdapter(stage, make(stage)) for stage in ("gap", "verify", "hypothesis", "execute", "evaluate", "report")]


class CriticalReviseReviewer(Reviewer):
    reviewer_id = "reviewer-critical-test-v1"

    def review(self, iteration: int, target_kind: str, target_id: str, artifact: dict[str, object]) -> ReviewerFinding:
        return ReviewerFinding(
            finding_id=f"critical:{iteration}:{target_kind}:{target_id}",
            reviewer_id=self.reviewer_id,
            target_kind=target_kind,  # type: ignore[arg-type]
            target_id=target_id,
            severity="critical",
            decision="revise",
            claim="Synthetic critical finding.",
            rationale="Regression test for policy-level critical stopping.",
            evidence_refs=["test:critical"],
        )


def test_critical_finding_stops_even_when_decision_is_revise(tmp_path: Path) -> None:
    store = SQLiteRunStore(tmp_path / "run.sqlite")
    panel = ReviewPanel([CriticalReviseReviewer(), DeterministicReviewer()])
    controller = AutonomousController(store, _adapters(), reviewers=panel)
    controller.create("critical-run", AutonomousRunConfig(max_iterations=1, stop_on_critical_review=True))

    state = controller.run("critical-run", {"provenance_refs": ["input:test"]})

    assert state.status == "failed"
    assert state.stop_reason == "Critical reviewer finding(s): 5"
    assert len(state.reviews) == 5
    assert all(review.critical_count == 1 for review in state.reviews)
    assert not any(stage.stage == "report" and stage.status == "succeeded" for stage in state.stage_executions)


def test_critical_review_can_be_configured_not_to_stop(tmp_path: Path) -> None:
    store = SQLiteRunStore(tmp_path / "run.sqlite")
    panel = ReviewPanel([CriticalReviseReviewer(), DeterministicReviewer()])
    controller = AutonomousController(store, _adapters(), reviewers=panel)
    controller.create("nonstop-run", AutonomousRunConfig(max_iterations=1, stop_on_critical_review=False))

    state = controller.run("nonstop-run", {"provenance_refs": ["input:test"]})

    assert state.status == "completed"
    assert len(state.reviews) == 5
