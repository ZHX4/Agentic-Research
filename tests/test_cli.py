from pathlib import Path

from typer.testing import CliRunner

from agentic_research.cli import app
from agentic_research.world_model.store import ScientificWorldModel

runner = CliRunner()


def test_cli_help_exposes_phase_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in [
        "search",
        "acquire",
        "parse",
        "analyze",
        "index",
        "retrieve",
        "traverse",
        "discover-gaps",
        "calibrate",
        "fit-calibrator",
    ]:
        assert command in result.stdout


def test_cli_demo_is_offline() -> None:
    result = runner.invoke(app, ["demo"])
    assert result.exit_code == 0
    assert "These are candidates only" in result.stdout


def test_discover_gaps_rejects_unknown_include_type(tmp_path: Path) -> None:
    database = tmp_path / "world.sqlite"
    with ScientificWorldModel(database):
        pass
    result = runner.invoke(
        app,
        [
            "discover-gaps",
            "--database",
            str(database),
            "--output",
            str(tmp_path / "gaps.json"),
            "--include-type",
            "bogus-detector",
        ],
    )
    assert result.exit_code != 0
