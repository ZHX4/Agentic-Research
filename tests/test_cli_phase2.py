import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_research.cli import app


def test_cli_help_exposes_phase2_commands() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "analyze" in result.stdout
    assert "calibrate" in result.stdout


def test_cli_calibrate(tmp_path: Path) -> None:
    input_path = tmp_path / "labels.jsonl"
    output_path = tmp_path / "report.json"
    input_path.write_text(
        json.dumps({"raw_confidence": 0.2, "correct": False})
        + "\n"
        + json.dumps({"raw_confidence": 0.9, "correct": True})
        + "\n",
        encoding="utf-8",
    )
    result = CliRunner().invoke(app, ["calibrate", "--input", str(input_path), "--output", str(output_path)])
    assert result.exit_code == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["sample_count"] == 2
