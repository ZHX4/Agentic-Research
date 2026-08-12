"""Confidence calibration utilities for extracted scientific claims."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field


class CalibrationExample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_confidence: float = Field(ge=0, le=1)
    correct: bool


class CalibrationBin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lower: float = Field(ge=0, le=1)
    upper: float = Field(ge=0, le=1)
    count: int = Field(ge=0)
    mean_confidence: float = Field(ge=0, le=1)
    empirical_accuracy: float = Field(ge=0, le=1)


class CalibrationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sample_count: int = Field(ge=0)
    expected_calibration_error: float = Field(ge=0, le=1)
    maximum_calibration_error: float = Field(ge=0, le=1)
    brier_score: float = Field(ge=0, le=1)
    bins: list[CalibrationBin] = Field(default_factory=list)


class IsotonicModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thresholds: list[float] = Field(min_length=1)
    values: list[float] = Field(min_length=1)


@dataclass(frozen=True)
class IsotonicCalibrator:
    """Monotone piecewise-constant calibration fitted by PAVA."""

    thresholds: list[float]
    values: list[float]

    @classmethod
    def fit(cls, examples: list[CalibrationExample]) -> "IsotonicCalibrator":
        if not examples:
            raise ValueError("At least one labeled calibration example is required")
        ordered = sorted(examples, key=lambda item: item.raw_confidence)
        blocks: list[list[float]] = [
            [item.raw_confidence, item.raw_confidence, 1.0 if item.correct else 0.0, 1.0]
            for item in ordered
        ]
        index = 0
        while index < len(blocks) - 1:
            if blocks[index][2] <= blocks[index + 1][2]:
                index += 1
                continue
            left, right = blocks[index], blocks[index + 1]
            count = left[3] + right[3]
            merged = [left[0], right[1], (left[2] * left[3] + right[2] * right[3]) / count, count]
            blocks[index:index + 2] = [merged]
            index = max(index - 1, 0)
        return cls(
            thresholds=[block[1] for block in blocks],
            values=[max(0.0, min(1.0, block[2])) for block in blocks],
        )

    @classmethod
    def from_model(cls, model: IsotonicModel) -> "IsotonicCalibrator":
        if len(model.thresholds) != len(model.values) or not model.thresholds:
            raise ValueError("thresholds and values must have the same non-zero length")
        if model.thresholds != sorted(model.thresholds):
            raise ValueError("thresholds must be sorted")
        return cls(thresholds=list(model.thresholds), values=list(model.values))

    def to_model(self) -> IsotonicModel:
        return IsotonicModel(thresholds=list(self.thresholds), values=list(self.values))

    def transform(self, raw_confidence: float) -> float:
        if not 0 <= raw_confidence <= 1:
            raise ValueError("raw_confidence must be within [0, 1]")
        for threshold, value in zip(self.thresholds, self.values):
            if raw_confidence <= threshold:
                return value
        return self.values[-1]


def calibration_report(examples: list[CalibrationExample], *, bins: int = 10) -> CalibrationReport:
    if bins < 1 or bins > 100:
        raise ValueError("bins must be between 1 and 100")
    if not examples:
        return CalibrationReport(sample_count=0, expected_calibration_error=0, maximum_calibration_error=0, brier_score=0)

    grouped: list[list[CalibrationExample]] = [[] for _ in range(bins)]
    for example in examples:
        index = min(int(example.raw_confidence * bins), bins - 1)
        grouped[index].append(example)

    output_bins: list[CalibrationBin] = []
    total = len(examples)
    ece = 0.0
    mce = 0.0
    brier = sum((example.raw_confidence - (1.0 if example.correct else 0.0)) ** 2 for example in examples) / total

    for index, group in enumerate(grouped):
        lower = index / bins
        upper = (index + 1) / bins
        if not group:
            output_bins.append(CalibrationBin(lower=lower, upper=upper, count=0, mean_confidence=0, empirical_accuracy=0))
            continue
        mean_confidence = sum(item.raw_confidence for item in group) / len(group)
        accuracy = sum(item.correct for item in group) / len(group)
        gap = abs(mean_confidence - accuracy)
        ece += len(group) / total * gap
        mce = max(mce, gap)
        output_bins.append(CalibrationBin(lower=lower, upper=upper, count=len(group), mean_confidence=mean_confidence, empirical_accuracy=accuracy))

    return CalibrationReport(
        sample_count=total,
        expected_calibration_error=ece,
        maximum_calibration_error=mce,
        brier_score=brier,
        bins=output_bins,
    )
