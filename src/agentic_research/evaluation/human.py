"""Human-evaluation aggregation and agreement metrics."""
from __future__ import annotations

from collections import defaultdict
from statistics import mean

from agentic_research.schemas.phase8 import HumanEvaluationResult, HumanRating, MetricValue

from .metrics import cohen_kappa, krippendorff_alpha_nominal


def evaluate_human_ratings(
    ratings: list[HumanRating],
    *,
    evaluation_id: str,
    task: str,
) -> HumanEvaluationResult:
    if task not in {"gap_quality", "novelty_verdict", "extraction_quality", "hypothesis_quality"}:
        raise ValueError("Unsupported human-evaluation task")
    if not ratings:
        raise ValueError("At least one human rating is required")
    by_case: dict[str, list[HumanRating]] = defaultdict(list)
    for rating in ratings:
        by_case[rating.case_id].append(rating)
    annotators = sorted({rating.annotator_id for rating in ratings})
    matrix: list[list[str | None]] = []
    for case_id in sorted(by_case):
        row_by_annotator = {rating.annotator_id: rating.label for rating in by_case[case_id]}
        matrix.append([row_by_annotator.get(annotator) for annotator in annotators])
    kappas: list[float] = []
    for left_idx in range(len(annotators)):
        for right_idx in range(left_idx + 1, len(annotators)):
            left = [row[left_idx] for row in matrix if row[left_idx] is not None and row[right_idx] is not None]
            right = [row[right_idx] for row in matrix if row[left_idx] is not None and row[right_idx] is not None]
            if left and right:
                kappas.append(cohen_kappa(left, right))
    agreement = [
        MetricValue(name="mean_pairwise_cohen_kappa", value=mean(kappas) if kappas else 0.0, n=len(kappas)),
        MetricValue(name="krippendorff_alpha_nominal", value=krippendorff_alpha_nominal(matrix), n=len(matrix)),
    ]
    numeric = [rating.score for rating in ratings if rating.score is not None]
    aggregate = [MetricValue(name="mean_human_score", value=mean(numeric), n=len(numeric))] if numeric else []
    return HumanEvaluationResult(
        evaluation_id=evaluation_id,
        task=task, annotator_count=len(annotators), item_count=len(by_case),
        agreement_metrics=agreement, aggregate_scores=aggregate, ratings=ratings,
    )
