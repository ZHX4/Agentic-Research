from pathlib import Path

from typer.testing import CliRunner

from agentic_research.cli import app


runner = CliRunner()


def test_demo_command_runs() -> None:
    result = runner.invoke(app, ["demo"])
    assert result.exit_code == 0, result.stdout
    assert "Candidate research gaps" in result.stdout


def test_validate_command_runs() -> None:
    result = runner.invoke(
        app,
        ["validate", "--input", str(Path("data/demo/papers.jsonl"))],
    )
    assert result.exit_code == 0, result.stdout
    assert "Validated" in result.stdout


def test_gaps_command_writes_json(tmp_path: Path) -> None:
    output = tmp_path / "gaps.json"
    result = runner.invoke(
        app,
        [
            "gaps",
            "--input",
            str(Path("data/demo/papers.jsonl")),
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert output.exists()
    assert "Wrote" in result.stdout
