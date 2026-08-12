"""Deterministic, dependency-light evaluation metrics."""
from __future__ import annotations

from collections import Counter
from math import log2
from statistics import mean
from typing import Iterable


def _safe_div(num: float, den: float) -> float:
    return 0.0 if den == 0 else num / den


def precision_recall_f1(predicted: Iterable[str], expected: Iterable[str]) -> tuple[float, float, float]:
    pred, gold = set(predicted), set(expected)
    tp = len(pred & gold)
    precision = _safe_div(tp, len(pred))
    recall = _safe_div(tp, len(gold))
    f1 = _safe_div(2 * precision * recall, precision + recall)
    return precision, recall, f1


def mean_reciprocal_rank(predictions: list[list[str]], expected: list[set[str]]) -> float:
    scores: list[float] = []
    for ranked, gold in zip(predictions, expected):
        rr = 0.0
        for rank, item in enumerate(ranked, start=1):
            if item in gold:
                rr = 1.0 / rank
                break
        scores.append(rr)
    return mean(scores) if scores else 0.0


def ndcg_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    if k <= 0:
        return 0.0
    dcg = sum((1.0 / log2(rank + 1)) for rank, item in enumerate(ranked[:k], start=1) if item in relevant)
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return _safe_div(dcg, idcg)


def average_precision_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    if not relevant or k <= 0:
        return 0.0
    hits = 0
    score = 0.0
    for rank, item in enumerate(ranked[:k], start=1):
        if item in relevant:
            hits += 1
            score += hits / rank
    return score / min(len(relevant), k)


def exact_match_accuracy(predicted: list[dict[str, str]], expected: list[dict[str, str]]) -> float:
    if len(predicted) != len(expected):
        raise ValueError("predicted and expected lengths must match")
    if not predicted:
        return 0.0
    return mean(1.0 if p == e else 0.0 for p, e in zip(predicted, expected))


def macro_field_f1(predicted: list[dict[str, str]], expected: list[dict[str, str]]) -> float:
    if len(predicted) != len(expected):
        raise ValueError("predicted and expected lengths must match")
    fields = sorted(set().union(*(item.keys() for item in expected), *(item.keys() for item in predicted))) if predicted or expected else []
    if not fields:
        return 0.0
    scores: list[float] = []
    for field in fields:
        pred = {item.get(field, "") for item in predicted}
        gold = {item.get(field, "") for item in expected}
        _, _, f1 = precision_recall_f1(pred, gold)
        scores.append(f1)
    return mean(scores)


def binary_classification_metrics(predicted: list[str], expected: list[str], positive: str) -> dict[str, float]:
    if len(predicted) != len(expected):
        raise ValueError("predicted and expected lengths must match")
    tp = sum(p == positive and e == positive for p, e in zip(predicted, expected))
    fp = sum(p == positive and e != positive for p, e in zip(predicted, expected))
    fn = sum(p != positive and e == positive for p, e in zip(predicted, expected))
    tn = sum(p != positive and e != positive for p, e in zip(predicted, expected))
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall)
    accuracy = _safe_div(tp + tn, len(expected))
    return {"precision": precision, "recall": recall, "f1": f1, "accuracy": accuracy}


def confusion_matrix(predicted: list[str], expected: list[str]) -> dict[tuple[str, str], int]:
    if len(predicted) != len(expected):
        raise ValueError("predicted and expected lengths must match")
    return dict(Counter(zip(expected, predicted)))


def cohen_kappa(labels_a: list[str], labels_b: list[str]) -> float:
    if len(labels_a) != len(labels_b):
        raise ValueError("rater label lengths must match")
    if not labels_a:
        return 0.0
    observed = mean(a == b for a, b in zip(labels_a, labels_b))
    categories = sorted(set(labels_a) | set(labels_b))
    p_a = Counter(labels_a)
    p_b = Counter(labels_b)
    expected = sum((p_a[c] / len(labels_a)) * (p_b[c] / len(labels_b)) for c in categories)
    return _safe_div(observed - expected, 1.0 - expected) if expected != 1.0 else 1.0


def krippendorff_alpha_nominal(ratings: list[list[str | None]]) -> float:
    """Nominal alpha for a rectangular item x annotator table; None means missing."""
    observed_pairs = 0
    disagreement = 0.0
    all_categories: set[str] = set()
    for row in ratings:
        values = [v for v in row if v is not None]
        all_categories.update(values)
        n = len(values)
        if n < 2:
            continue
        for i in range(n):
            for j in range(i + 1, n):
                observed_pairs += 1
                disagreement += 0.0 if values[i] == values[j] else 1.0
    if observed_pairs == 0:
        return 0.0
    Do = disagreement / observed_pairs
    flat = [v for row in ratings for v in row if v is not None]
    counts = Counter(flat)
    total = len(flat)
    if total < 2:
        return 0.0
    expected_disagreement = 1.0 - sum((count / total) ** 2 for count in counts.values())
    return 1.0 - _safe_div(Do, expected_disagreement) if expected_disagreement else 1.0


def paired_delta(baseline: list[float], treatment: list[float]) -> dict[str, float]:
    if len(baseline) != len(treatment):
        raise ValueError("paired samples must have equal length")
    if not baseline:
        return {"mean_delta": 0.0, "relative_delta": 0.0}
    deltas = [t - b for b, t in zip(baseline, treatment)]
    base_mean = mean(baseline)
    return {"mean_delta": mean(deltas), "relative_delta": _safe_div(mean(deltas), abs(base_mean))}


def bootstrap_mean_ci(values: list[float], *, samples: int = 2000, alpha: float = 0.05, seed: int = 0) -> tuple[float, float]:
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0, 1)")
    if not values:
        return 0.0, 0.0
    state = seed & 0xFFFFFFFF
    draws: list[float] = []
    n = len(values)
    for _ in range(samples):
        sample: list[float] = []
        for _ in range(n):
            state = (1664525 * state + 1013904223) & 0xFFFFFFFF
            sample.append(values[state % n])
        draws.append(mean(sample))
    draws.sort()
    lo = draws[max(0, int((alpha / 2) * len(draws)) - 1)]
    hi = draws[min(len(draws) - 1, int((1 - alpha / 2) * len(draws)))]
    return lo, hi


def temporal_leakage(prediction_years: dict[str, int | None], cutoff_year: int) -> dict[str, float]:
    if cutoff_year < 1900:
        raise ValueError("cutoff_year is invalid")
    total = len(prediction_years)
    future = sum(year is not None and year > cutoff_year for year in prediction_years.values())
    unknown = sum(year is None for year in prediction_years.values())
    return {
        "leakage_rate": _safe_div(future, total),
        "future_items": float(future),
        "unknown_year_items": float(unknown),
        "total_items": float(total),
    }
