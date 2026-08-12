"""Deterministic Phase 6 hypothesis generation and selection."""
from __future__ import annotations

import hashlib
import itertools
import json

from agentic_research.schemas.gap import GapCandidate, GapStatus
from agentic_research.schemas.phase6 import (
    Hypothesis,
    HypothesisCandidate,
    HypothesisConfig,
    HypothesisReflection,
    HypothesisRun,
)

from .diversity import cluster_hypotheses, similarity


def _id(prefix: str, *parts: str) -> str:
    payload = "||".join(parts).encode("utf-8")
    return f"{prefix}:{hashlib.sha256(payload).hexdigest()[:20]}"


def _allowed(gaps: list[GapCandidate], cfg: HypothesisConfig) -> list[GapCandidate]:
    if cfg.min_gap_status is GapStatus.SURVIVED:
        allowed = {GapStatus.SURVIVED}
    elif cfg.min_gap_status is GapStatus.WEAKENED:
        allowed = {GapStatus.SURVIVED, GapStatus.WEAKENED}
    else:
        allowed = {GapStatus.SURVIVED, GapStatus.WEAKENED, GapStatus.UNCERTAIN}
    return [gap for gap in gaps if gap.status in allowed]


def _scores(gap: GapCandidate) -> tuple[float, float, float, float]:
    status = {
        GapStatus.SURVIVED: 1.0,
        GapStatus.WEAKENED: 0.55,
        GapStatus.UNCERTAIN: 0.35,
    }.get(gap.status, 0.0)
    evidence = min(1.0, gap.support_count / 5.0)
    novelty = min(1.0, 0.45 + 0.35 * gap.confidence + 0.20 * status)
    significance = min(1.0, 0.45 + 0.35 * gap.structural_support + 0.20 * evidence)
    coverage = gap.coverage_ratio if gap.coverage_ratio is not None else 0.5
    feasibility = min(1.0, 0.55 + 0.25 * status + 0.20 * (1.0 - coverage))
    return novelty, evidence, significance, feasibility


def reflect(h: Hypothesis) -> HypothesisReflection:
    weaknesses: list[str] = []
    if h.feasibility_score < 0.55:
        weaknesses.append("Feasibility is limited.")
    if h.novelty_score < 0.55:
        weaknesses.append("Novelty confidence depends on upstream gap evidence.")
    score = max(
        0.0,
        min(
            1.0,
            0.55
            + 0.20 * h.evidence_score
            + 0.15 * h.feasibility_score
            - 0.08 * len(weaknesses),
        ),
    )
    recommendation = (
        "advance" if score >= 0.72 and not weaknesses else "revise" if score >= 0.50 else "discard"
    )
    return HypothesisReflection(
        reflection_id=_id("reflect", h.hypothesis_id),
        hypothesis_id=h.hypothesis_id,
        strengths=[
            "Linked to a verified upstream gap.",
            "Contains an explicit falsification condition.",
        ],
        weaknesses=weaknesses,
        hidden_assumptions=h.assumptions
        or ["The proposed mechanism can be isolated from implementation artifacts."],
        confounders=[
            "Dataset and baseline choice may confound effects.",
            "Hyperparameters and compute budgets may confound comparisons.",
        ],
        failure_modes=[h.falsification_condition],
        score=score,
        recommendation=recommendation,
    )


def _build(
    gap: GapCandidate,
    origin: str,
    mechanism: str,
    effect: str,
    reject: str,
    assumptions: list[str],
    predicted: list[str],
    ordinal: int,
) -> HypothesisCandidate:
    novelty, evidence, significance, feasibility = _scores(gap)
    method = gap.method or "the target method"
    dataset = gap.dataset or "the target dataset"
    task = gap.task or "the target task"
    hypothesis = Hypothesis(
        hypothesis_id=_id("hyp", gap.gap_id, origin, str(ordinal), mechanism),
        statement=(
            f"For {task}, applying {method} to {dataset} will produce "
            "the predicted effect under the stated controls."
        ),
        research_question=(
            f"Does {method} produce the predicted effect on {dataset} "
            f"for {task} under a controlled protocol?"
        ),
        source_gap_ids=[gap.gap_id],
        source_statuses=[gap.status],
        origin=origin,
        mechanism=mechanism,
        expected_effect=effect,
        falsification_condition=reject,
        assumptions=assumptions,
        predicted_observations=predicted,
        novelty_score=novelty,
        evidence_score=evidence,
        significance_score=significance,
        feasibility_score=feasibility,
        diversity_score=1.0,
        robustness_score=0.55,
        reflection_score=0.5,
    )
    reflection = reflect(hypothesis)
    return HypothesisCandidate(
        hypothesis=hypothesis.model_copy(update={"reflection_score": reflection.score}),
        reflection=reflection,
    )


def generate_candidates(
    gaps: list[GapCandidate], config: HypothesisConfig | None = None
) -> list[HypothesisCandidate]:
    cfg = config or HypothesisConfig()
    output: list[HypothesisCandidate] = []
    templates = [
        (
            "gap_direct",
            "directly test the missing configuration",
            "a measurable improvement",
            "reject if no improvement over the strongest baseline",
            ["The configuration is technically realizable."],
            ["The effect is stable across seeds."],
        ),
        (
            "gap_conservative",
            "isolate the narrowest causal mechanism",
            "a smaller reproducible attributable effect",
            "reject if the effect disappears under a matched control",
            ["Only one causal factor changes."],
            ["Matched-control results support the mechanism."],
        ),
        (
            "gap_high_risk",
            "map interaction or failure-boundary behavior",
            "an interaction effect or systematic boundary",
            "reject if the interaction is indistinguishable from controls",
            ["The interaction can be isolated."],
            ["The boundary is reproducible."],
        ),
        (
            "gap_composed",
            "combine the candidate configuration with an adjacent technique",
            "an incremental effect beyond both components",
            "reject if no incremental benefit remains under matched controls",
            ["The adjacent technique is reproducible."],
            ["Ablation isolates the candidate contribution."],
        ),
        (
            "gap_conservative",
            "replicate under a preregistered protocol",
            "a reproducible result or tight bound",
            "reject if the result is not reproducible across matched seeds",
            ["Primary metrics are fixed before analysis."],
            ["Replication variance remains within tolerance."],
        ),
        (
            "gap_high_risk",
            "stress-test the candidate across controlled regimes",
            "a reproducible robustness boundary or regime-specific effect",
            "reject if the apparent effect vanishes under controlled perturbations",
            ["The perturbation grid is defined before evaluation."],
            ["The effect or failure boundary persists across perturbations."],
        ),
    ]

    usable_templates = templates[: cfg.hypotheses_per_gap]
    for gap in sorted(_allowed(gaps, cfg), key=lambda item: item.gap_id):
        for ordinal, template in enumerate(usable_templates):
            item = _build(gap, *template, ordinal)
            if any(
                similarity(item.hypothesis.statement, existing.hypothesis.statement)
                >= cfg.dedup_similarity_threshold
                for existing in output
            ):
                continue
            diversity = 1.0
            if output:
                diversity = 1.0 - max(
                    similarity(item.hypothesis.statement, existing.hypothesis.statement)
                    for existing in output
                )
            item = item.model_copy(
                update={
                    "hypothesis": item.hypothesis.model_copy(update={"diversity_score": diversity})
                }
            )
            output.append(item)

    source = [item.hypothesis for item in output if item.reflection.recommendation != "discard"]
    added = 0
    for left, right in itertools.combinations(source, 2):
        if set(left.source_gap_ids) & set(right.source_gap_ids):
            continue
        if added >= cfg.max_composed_pairs:
            break
        gap_ids = sorted(set(left.source_gap_ids + right.source_gap_ids))
        synthetic_gap = GapCandidate(
            gap_id="::".join(gap_ids),
            gap_type="cross_domain",
            statement="composed",
            confidence=min(left.evidence_score, right.evidence_score),
            support_count=1,
            structural_support=0.5,
            rationale="composed from independent verified gaps",
            status=GapStatus.SURVIVED,
        )
        item = _build(
            synthetic_gap,
            "gap_composed",
            f"Combine: {left.mechanism} AND {right.mechanism}",
            "an incremental interaction effect",
            "reject if the joint system does not outperform both constituents",
            sorted(set(left.assumptions + right.assumptions)),
            ["Interaction survives matched-control analysis."],
            added,
        )
        hypothesis = item.hypothesis.model_copy(
            update={
                "source_gap_ids": gap_ids,
                "source_statuses": sorted(
                    set(left.source_statuses + right.source_statuses), key=lambda status: status.value
                ),
            }
        )
        item = item.model_copy(update={"hypothesis": hypothesis})
        if not any(
            similarity(hypothesis.statement, existing.hypothesis.statement)
            >= cfg.dedup_similarity_threshold
            for existing in output
        ):
            output.append(item)
            added += 1
    return output


def _dominates(a: Hypothesis, b: Hypothesis) -> bool:
    left = (a.novelty_score, a.significance_score, a.feasibility_score)
    right = (b.novelty_score, b.significance_score, b.feasibility_score)
    return all(x >= y for x, y in zip(left, right, strict=True)) and any(
        x > y for x, y in zip(left, right, strict=True)
    )


def pareto_frontier(items: list[HypothesisCandidate]) -> list[HypothesisCandidate]:
    frontier = [
        item
        for item in items
        if not any(
            _dominates(other.hypothesis, item.hypothesis)
            for other in items
            if other.hypothesis.hypothesis_id != item.hypothesis.hypothesis_id
        )
    ]
    return sorted(
        frontier,
        key=lambda item: (-item.hypothesis.composite_score, item.hypothesis.hypothesis_id),
    )


def _evolve(item: HypothesisCandidate, generation: int) -> HypothesisCandidate:
    hypothesis = item.hypothesis.model_copy(
        update={
            "hypothesis_id": _id("hyp-evolved", item.hypothesis.hypothesis_id, str(generation)),
            "origin": "evolved",
            "mechanism": item.hypothesis.mechanism + " Add an explicit matched control.",
            "falsification_condition": item.hypothesis.falsification_condition
            + " Also reject if the effect disappears under that control.",
            "robustness_score": min(1.0, item.hypothesis.robustness_score + 0.08),
        }
    )
    reflection = reflect(hypothesis)
    return HypothesisCandidate(
        hypothesis=hypothesis.model_copy(update={"reflection_score": reflection.score}),
        reflection=reflection,
    )


def _tournament(items: list[HypothesisCandidate], cfg: HypothesisConfig) -> list[HypothesisCandidate]:
    pool = sorted(
        items,
        key=lambda item: (-item.hypothesis.composite_score, item.hypothesis.hypothesis_id),
    )
    for _ in range(cfg.tournament_rounds):
        winners: list[HypothesisCandidate] = []
        for start in range(0, len(pool), cfg.tournament_size):
            group = pool[start : start + cfg.tournament_size]
            if group:
                winners.append(
                    max(
                        group,
                        key=lambda item: (
                            item.hypothesis.composite_score,
                            item.reflection.score,
                            item.hypothesis.hypothesis_id,
                        ),
                    )
                )
        pool = winners
    return pool[: cfg.keep_diverse_limit]


def run_hypothesis_reasoning(
    gaps: list[GapCandidate], config: HypothesisConfig | None = None
) -> HypothesisRun:
    cfg = config or HypothesisConfig()
    initial = generate_candidates(gaps, cfg)
    pool = [item for item in initial if item.reflection.recommendation != "discard"]
    evolved: list[HypothesisCandidate] = []

    for generation in range(1, cfg.max_evolution_generations + 1):
        new = [_evolve(item, generation) for item in pool[: cfg.evolve_top_k]]
        evolved.extend(new)
        pool = _tournament(pool + new, cfg)

    by_id = {item.hypothesis.hypothesis_id: item for item in initial + evolved}
    candidates = [by_id[key] for key in sorted(by_id)]
    clusters = cluster_hypotheses(candidates, cfg.clustering_threshold) if candidates else []
    frontier = pareto_frontier(pool)[: cfg.pareto_limit]
    run_id = _id(
        "hypothesis-run",
        *sorted(gap.gap_id for gap in gaps),
        json.dumps(cfg.model_dump(mode="json"), sort_keys=True),
    )
    return HypothesisRun(
        run_id=run_id,
        input_gap_ids=sorted(gap.gap_id for gap in gaps),
        initial_generated_count=len(initial),
        evolved_count=len(evolved),
        generated_count=len(candidates),
        reflected_count=len(candidates),
        selected_count=len(pool),
        pareto_count=len(frontier),
        cluster_count=len(clusters),
        candidates=candidates,
        pareto_frontier_ids=[item.hypothesis.hypothesis_id for item in frontier],
        selected_hypothesis_ids=[item.hypothesis.hypothesis_id for item in pool[: cfg.keep_diverse_limit]],
        warnings=[] if initial else ["No eligible verified gaps produced hypotheses."],
    )
