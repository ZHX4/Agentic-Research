"""PEFT-30 adapters into existing Phase 8 evaluation machinery.

Reuses BenchmarkCase / PredictionRecord / HumanRating and the existing
evaluate_* / evaluate_human_ratings functions. This module only adapts
shapes; it never reimplements metric formulas.
"""

from __future__ import annotations

import hashlib
from typing import Literal

from agentic_research.evaluation.engine import (
    evaluate_labels,
    evaluate_retrieval,
    evaluate_temporal,
)
from agentic_research.evaluation.human import evaluate_human_ratings
from agentic_research.schemas.phase8 import (
    BenchmarkCase,
    BenchmarkResult,
    HumanEvaluationResult,
    HumanRating,
    PredictionRecord,
)

from .annotations import AdjudicatedAnnotation
from .manifest import CUTOFF_YEAR

HumanTask = Literal["gap_quality", "novelty_verdict", "extraction_quality", "hypothesis_quality"]


def _input_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def gap_cases_from_adjudicated(
    records: list[AdjudicatedAnnotation],
) -> list[BenchmarkCase]:
    cases: list[BenchmarkCase] = []
    for record in records:
        if record.kind != "gap":
            continue
        cases.append(
            BenchmarkCase(
                case_id=record.case_id,
                kind="gap",
                input_hash=_input_hash(record.case_id),
                expected_labels=[record.final_label],
                metadata={"benchmark": "sci-bench-peft30-v1"},
            )
        )
    return cases


def novelty_cases_from_adjudicated(
    records: list[AdjudicatedAnnotation],
) -> list[BenchmarkCase]:
    cases: list[BenchmarkCase] = []
    for record in records:
        if record.kind != "novelty":
            continue
        cases.append(
            BenchmarkCase(
                case_id=record.case_id,
                kind="novelty",
                input_hash=_input_hash(record.case_id),
                expected_labels=[record.final_label],
                metadata={"benchmark": "sci-bench-peft30-v1"},
            )
        )
    return cases


def retrieval_cases(case_ids: list[str], expected: dict[str, list[str]]) -> list[BenchmarkCase]:
    return [
        BenchmarkCase(
            case_id=case_id,
            kind="retrieval",
            input_hash=_input_hash(case_id),
            expected_ids=expected.get(case_id, []),
            metadata={"benchmark": "sci-bench-peft30-v1"},
        )
        for case_id in case_ids
    ]


def temporal_cases(case_ids: list[str]) -> list[BenchmarkCase]:
    return [
        BenchmarkCase(
            case_id=case_id,
            kind="temporal",
            input_hash=_input_hash(case_id),
            cutoff_year=CUTOFF_YEAR,
            metadata={"benchmark": "sci-bench-peft30-v1"},
        )
        for case_id in case_ids
    ]


def predictions_from_labels(mapping: dict[str, str]) -> list[PredictionRecord]:
    return [
        PredictionRecord(case_id=case_id, predicted_labels=[label])
        for case_id, label in mapping.items()
    ]


def run_gap_evaluation(
    records: list[AdjudicatedAnnotation],
    predictions: list[PredictionRecord],
    *,
    system_name: str,
    positive: str | None = None,
) -> BenchmarkResult:
    return evaluate_labels(
        gap_cases_from_adjudicated(records),
        predictions,
        kind="gap",
        system_name=system_name,
        benchmark_id="sci-bench-peft30-v1-gap",
        positive=positive,
    )


def run_novelty_evaluation(
    records: list[AdjudicatedAnnotation],
    predictions: list[PredictionRecord],
    *,
    system_name: str,
    positive: str | None = None,
) -> BenchmarkResult:
    return evaluate_labels(
        novelty_cases_from_adjudicated(records),
        predictions,
        kind="novelty",
        system_name=system_name,
        benchmark_id="sci-bench-peft30-v1-novelty",
        positive=positive,
    )


def run_retrieval_evaluation(
    case_ids: list[str],
    expected: dict[str, list[str]],
    predictions: list[PredictionRecord],
    *,
    system_name: str,
) -> BenchmarkResult:
    return evaluate_retrieval(
        retrieval_cases(case_ids, expected),
        predictions,
        system_name=system_name,
        benchmark_id="sci-bench-peft30-v1-retrieval",
    )


def run_temporal_evaluation(
    case_ids: list[str],
    predictions: list[PredictionRecord],
    *,
    system_name: str,
) -> BenchmarkResult:
    return evaluate_temporal(
        temporal_cases(case_ids),
        predictions,
        system_name=system_name,
        benchmark_id="sci-bench-peft30-v1-temporal",
    )


def human_ratings_from_adjudicated(
    records: list[AdjudicatedAnnotation],
) -> list[HumanRating]:
    """Adapter: A/B labels become two HumanRatings per case (trail preserved)."""
    ratings: list[HumanRating] = []
    for record in records:
        ratings.append(
            HumanRating(
                case_id=record.case_id,
                annotator_id=record.annotation_a.annotator_id,
                label=record.annotation_a.label,
                rationale=record.annotation_a.rationale,
            )
        )
        ratings.append(
            HumanRating(
                case_id=record.case_id,
                annotator_id=record.annotation_b.annotator_id,
                label=record.annotation_b.label,
                rationale=record.annotation_b.rationale,
            )
        )
    return ratings


def run_agreement(
    records: list[AdjudicatedAnnotation],
    *,
    task: HumanTask = "gap_quality",
) -> HumanEvaluationResult:
    return evaluate_human_ratings(
        human_ratings_from_adjudicated(records),
        evaluation_id="sci-bench-peft30-v1-agreement-" + task,
        task=task,
    )
