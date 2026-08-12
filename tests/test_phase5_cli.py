from pathlib import Path

from typer.testing import CliRunner

from agentic_research.schemas.gap import GapCandidate
from agentic_research.schemas.phase4 import GapDiscoveryResult, GapSignal
from agentic_research.verification.cli import app


runner = CliRunner()


def _input_file(tmp_path: Path) -> Path:
    candidate = GapCandidate(
        gap_id="gap-cli",
        gap_type="missing_combination",
        statement="Method Alpha on Dataset Beta is absent.",
        method="Method Alpha",
        dataset="Dataset Beta",
        evidence_paper_ids=["p1", "p2"],
        signal_ids=["s1"],
        support_count=2,
        structural_support=0.5,
        confidence=0.5,
        rationale="candidate",
    )
    result = GapDiscoveryResult(
        run_id="run-cli",
        corpus_paper_count=2,
        signals=[
            GapSignal(
                signal_id="s1",
                gap_type="missing_combination",
                statement=candidate.statement,
                paper_ids=["p1", "p2"],
                entity_values={"method": "Method Alpha", "dataset": "Dataset Beta"},
                support_count=2,
                structural_score=0.5,
            )
        ],
        candidates=[candidate],
    )
    path = tmp_path / "gaps.json"
    path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return path


def test_verify_cli_local_requires_database_or_explicit_no_local(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "verify-gaps",
            "--input", str(_input_file(tmp_path)),
            "--output", str(tmp_path / "out.json"),
            "--no-external",
        ],
    )
    assert result.exit_code != 0
    assert "database" in result.output.lower()


def test_verify_cli_external_only_can_write_inconclusive_report(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    result = runner.invoke(
        app,
        [
            "verify-gaps",
            "--input", str(_input_file(tmp_path)),
            "--output", str(output),
            "--no-local",
        ],
    )
    assert result.exit_code == 0
    assert output.exists()
