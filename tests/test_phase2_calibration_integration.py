import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_research.cli import app
from agentic_research.intelligence.calibration import CalibrationExample, IsotonicCalibrator


def test_isotonic_model_round_trip() -> None:
    calibrator = IsotonicCalibrator.fit([
        CalibrationExample(raw_confidence=0.1, correct=False),
        CalibrationExample(raw_confidence=0.9, correct=True),
    ])
    restored = IsotonicCalibrator.from_model(calibrator.to_model())
    assert restored.transform(0.1) == calibrator.transform(0.1)
    assert restored.transform(0.9) == calibrator.transform(0.9)


def test_cli_fit_calibrator(tmp_path: Path) -> None:
    labels = tmp_path / "labels.jsonl"
    output = tmp_path / "model.json"
    labels.write_text(
        json.dumps({"raw_confidence": 0.1, "correct": False}) + "\n"
        + json.dumps({"raw_confidence": 0.9, "correct": True}) + "\n",
        encoding="utf-8",
    )
    result = CliRunner().invoke(app, ["fit-calibrator", "--input", str(labels), "--output", str(output)])
    assert result.exit_code == 0
    model = json.loads(output.read_text(encoding="utf-8"))
    assert model["thresholds"]
    assert model["values"]
