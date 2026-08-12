from typer.testing import CliRunner

from agentic_research.cli import app


runner = CliRunner()


def test_cli_help_exposes_phase1_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "search" in result.stdout
    assert "acquire" in result.stdout
    assert "parse" in result.stdout


def test_cli_demo_is_offline() -> None:
    result = runner.invoke(app, ["demo"])
    assert result.exit_code == 0
    assert "These are candidates only" in result.stdout
