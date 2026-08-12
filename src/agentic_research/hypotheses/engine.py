"""Deterministic Phase 6 hypothesis factory, reflection, ranking and evolution."""
from __future__ import annotations

import hashlib
import itertools
import re
from typing import Final

from agentic_research.schemas.gap import GapCandidate, GapStatus
from agentic_research.schemas.phase6 import Hypothesis, HypothesisCandidate, HypothesisConfig, HypothesisReflection, HypothesisRun

_DIMENSIONS: Final = ("novelty_score", "significance_score", "feasibility_score")


def _id(prefix: str, *parts: str) -> str:
    return f"{prefix}:{hashlib.sha256('||'.join(parts).encode()).hexdigest()[:20]}"


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.casefold(), flags=re.UNICODE))


def _sim(a: str, b: str) -> float:
    x, y = _tokens(a), _tokens(b)
    if not x and not y:
        return 1.0
    if not x or not y:
        return 0.0
    return len(x & y) / len(x | y)


def _eligible(gaps: list[GapCandidate], cfg: HypothesisConfig) -> list[GapCandidate]:
    if cfg.min_gap_status == GapStatus.SURVIVED:
        allowed = {GapStatus.SURVIVED}
    elif cfg.min_gap_status == GapStatus.WEAKENED:
        allowed = {GapStatus.SURVIVED, GapStatus.WEAKENED}
    elif cfg.min_gap_status == GapStatus.UNCERTAIN and cfg.allow_uncertain_gaps:
        allowed = {GapStatus.SURVIVED, GapStatus.WEAKENED, GapStatus.UNCERTAIN}
    else:
        allowed = {GapStatus.SURVIVED}
    return [g for g in gaps if g.status in allowed]


def _scores(gap: GapCandidate) -> tuple[float, float, float, float]:
    status = {GapStatus.SURVIVED: 1.0, GapStatus.WEAKENED: 0.55, GapStatus.UNCERTAIN: 0.35}.get(gap.status, 0.0)
    evidence = min(1.0, gap.support_count / 5.0)
    novelty = min(1.0, 0.45 + 0.35 * gap.confidence + 0.20 * status)
    significance = min(1.0, 0.45 + 0.35 * gap.structural_support + 0.20 * evidence)
    coverage = gap.coverage_ratio if gap.coverage_ratio is not None else 0.5
    feasibility = min(1.0, 0.55 + 0.25 * status + 0.20 * (1.0 - coverage))
    return novelty, evidence, significance, feasibility


def _templates(gap: GapCandidate) -> list[tuple[str, str, str, str, list[str], list[str]]]:
    m = gap.method or "the target method"
    d = gap.dataset or "the target dataset"
    t = gap.task or "the target task"
    return [
        ("gap_direct", f"Apply {m} to {d} for {t} under a controlled protocol.", f"{m} will improve the primary metric for {t}.", f"Reject if {m} fails to improve the primary metric over the strongest baseline across seeds.", ["The configuration is technically realizable."], ["The effect is stable across seeds."]),
        ("gap_conservative", f"Test the narrowest mechanism connecting {m} with {t} on {d}.", "A constrained intervention produces a reproducible attributable effect.", "Reject if the effect disappears under a matched control.", ["Only one causal factor changes at a time."], ["Matched-control results support the mechanism."]),
        ("gap_high_risk", f"Map whether {m} interacts with properties of {d} in the {t} regime.", "The interaction reveals an effect or systematic failure boundary.", "Reject if the interaction is indistinguishable from matched controls.", ["The interaction can be isolated."], ["The boundary is reproducible."]),
        ("gap_composed", f"Combine the candidate configuration with an adjacent technique while isolating {m}'s contribution.", "The composition yields an incremental effect beyond its parts.", "Reject if the joint system offers no incremental benefit.", ["The adjacent technique is reproducible."], ["Ablation isolates the candidate contribution."]),
        ("gap_conservative", f"Replicate the candidate configuration for {t} with a preregistered protocol.", "Replication confirms or tightly bounds the missing result.", "Reject if the effect is not reproducible under matched seeds.", ["Primary metrics and seeds are fixed before analysis."], ["Replication variance remains within tolerance."]),
    ]


def reflect(h: Hypothesis) -> HypothesisReflection:
    weaknesses: list[str] = []
    if h.feasibility_score < 0.55:
        weaknesses.append("Feasibility is limited.")
    if h.novelty_score < 0.55:
        weaknesses.append("Novelty confidence depends on upstream gap evidence.")
    assumptions = h.assumptions or ["The proposed mechanism can be isolated from implementation artifacts."]
    score = max(0.0, min(1.0, 0.55 + 0.20 * h.evidence_score + 0.15 * h.feasibility_score - 0.08 * len(weaknesses)))
    recommendation = "advance" if score >= 0.72 and not weaknesses else "revise" if score >= 0.50 else "discard"
    return HypothesisReflection(
        reflection_id=_id("reflect", h.hypothesis_id),
        hypothesis_id=h.hypothesis_id,
        strengths=["Linked to a verified upstream gap.", "Contains an explicit falsification condition."],
        weaknesses=weaknesses,
        hidden_assumptions=sorted(set(assumptions)),
        confounders=["Dataset and baseline choice may explain effects.", "Hyperparameters and compute budgets may confound comparisons."],
        failure_modes=[h.falsification_condition],
        score=score,
        recommendation=recommendation,
    )


def _hypothesis(gap: GapCandidate, tpl: tuple[str, str, str, str, list[str], list[str]], i: int) -> Hypothesis:
    origin, mechanism, effect, falsification, assumptions, predicted = tpl
    novelty, evidence, significance, feasibility = _scores(gap)
    m, d, t = gap.method or "the target method", gap.dataset or "the target dataset", gap.task or "the target task"
    return Hypothesis(
        hypothesis_id=_id("hyp", gap.gap_id, origin, str(i), mechanism),
        statement=f"For {t}, applying {m} to {d} will produce the predicted effect under the stated controls.",
        research_question=f"Does {m} produce the predicted effect on {d} for {t} under a controlled protocol?",
        source_gap_ids=[gap.gap_id], source_statuses=[gap.status], origin=origin, mechanism=mechanism,
        expected_effect=effect, falsification_condition=falsification, assumptions=assumptions,
        predicted_observations=predicted, novelty_score=novelty, evidence_score=evidence,
        significance_score=significance, feasibility_score=feasibility, diversity_score=0.5,
        robustness_score=0.55, reflection_score=0.5,
    )


def _dominates(a: Hypothesis, b: Hypothesis) -> bool:
    av = [getattr(a, k) for k in _DIMENSIONS]; bv = [getattr(b, k) for k in _DIMENSIONS]
    return all(x >= y for x, y in zip(av, bv)) and any(x > y for x, y in zip(av, bv))


def pareto_frontier(items: list[HypothesisCandidate]) -> list[HypothesisCandidate]:
    out = [x for x in items if not any(_dominates(y.hypothesis, x.hypothesis) for y in items if y.hypothesis.hypothesis_id != x.hypothesis.hypothesis_id)]
    return sorted(out, key=lambda x: (-x.hypothesis.composite_score, x.hypothesis.hypothesis_id))


def _tournament(items: list[HypothesisCandidate], cfg: HypothesisConfig) -> list[HypothesisCandidate]:
    pool = sorted(items, key=lambda x: (-x.hypothesis.composite_score, x.hypothesis.hypothesis_id))
    for _ in range(cfg.tournament_rounds):
        winners = []
        for i in range(0, len(pool), cfg.tournament_size):
            group = pool[i:i + cfg.tournament_size]
            if group:
                winners.append(max(group, key=lambda x: (x.hypothesis.composite_score, x.reflection.score, x.hypothesis.hypothesis_id)))
        pool = winners
    return pool[:cfg.keep_diverse_limit]


def _evolve(item: HypothesisCandidate, generation: int) -> HypothesisCandidate:
    h = item.hypothesis.model_copy(update={
        "hypothesis_id": _id("hyp-evolved", item.hypothesis.hypothesis_id, str(generation)),
        "origin": "evolved",
        "mechanism": item.hypothesis.mechanism + " The evolved version adds an explicit matched control.",
        "falsification_condition": item.hypothesis.falsification_condition + " Also reject if the effect disappears under the matched control.",
        "robustness_score": min(1.0, item.hypothesis.robustness_score + 0.08),
    })
    r = reflect(h)
    return HypothesisCandidate(hypothesis=h.model_copy(update={"reflection_score": r.score}), reflection=r)


def generate_candidates(gaps: list[GapCandidate], config: HypothesisConfig | None = None) -> list[HypothesisCandidate]:
    cfg = config or HypothesisConfig(); generated: list[HypothesisCandidate] = []; accepted: list[Hypothesis] = []
    for gap in sorted(_eligible(gaps, cfg), key=lambda g: g.gap_id):
        for i, tpl in enumerate(_templates(gap)[:cfg.hypotheses_per_gap]):
            h = _hypothesis(gap, tpl, i)
            h = h.model_copy(update={"diversity_score": 1.0 if not accepted else 1.0 - max(_sim(h.statement, x.statement) for x in accepted)})
            r = reflect(h); h = h.model_copy(update={"reflection_score": r.score})
            if any(_sim(h.statement, x.statement) >= cfg.dedup_similarity_threshold for x in accepted):
                continue
            generated.append(HypothesisCandidate(hypothesis=h, reflection=r)); accepted.append(h)

    pair_count = 0
    source = [x.hypothesis for x in generated if x.reflection.recommendation != "discard"]
    for left, right in itertools.combinations(source, 2):
        if pair_count >= cfg.max_composed_pairs or set(left.source_gap_ids) & set(right.source_gap_ids):
            continue
        h = Hypothesis(
            hypothesis_id=_id("hyp-composed", left.hypothesis_id, right.hypothesis_id),
            statement=f"The mechanisms from {left.hypothesis_id} and {right.hypothesis_id} have an incremental interaction that survives matched controls.",
            research_question=f"Does the interaction between {left.hypothesis_id} and {right.hypothesis_id} produce an incremental effect?",
            source_gap_ids=sorted(set(left.source_gap_ids + right.source_gap_ids)),
            source_statuses=sorted(set(left.source_statuses + right.source_statuses), key=lambda s: s.value),
            origin="gap_composed", mechanism=f"Combine: {left.mechanism} AND {right.mechanism}",
            expected_effect="An incremental interaction effect beyond each component alone.",
            falsification_condition="Reject if the joint system does not outperform both constituents under matched controls.",
            assumptions=sorted(set(left.assumptions + right.assumptions)), predicted_observations=["Interaction survives ablation."],
            novelty_score=(left.novelty_score + right.novelty_score) / 2, evidence_score=min(left.evidence_score, right.evidence_score),
            significance_score=(left.significance_score + right.significance_score) / 2, feasibility_score=min(left.feasibility_score, right.feasibility_score) * 0.9,
            diversity_score=1.0 - _sim(left.statement, right.statement), robustness_score=min(left.robustness_score, right.robustness_score), reflection_score=0.5,
        )
        r = reflect(h); h = h.model_copy(update={"reflection_score": r.score})
        if not any(_sim(h.statement, x.hypothesis.statement) >= cfg.dedup_similarity_threshold for x in generated):
            generated.append(HypothesisCandidate(hypothesis=h, reflection=r)); pair_count += 1
    return generated


def run_hypothesis_reasoning(gaps: list[GapCandidate], config: HypothesisConfig | None = None) -> HypothesisRun:
    cfg = config or HypothesisConfig(); generated = generate_candidates(gaps, cfg)
    selected = _tournament([x for x in generated if x.reflection.recommendation != "discard"], cfg)
    for generation in range(1, cfg.max_evolution_generations + 1):
        combined = selected + [_evolve(x, generation) for x in selected[:cfg.evolve_top_k]]
        deduped: list[HypothesisCandidate] = []
        for item in sorted(combined, key=lambda x: (-x.hypothesis.composite_score, x.hypothesis.hypothesis_id)):
            if not any(_sim(item.hypothesis.statement, x.hypothesis.statement) >= cfg.dedup_similarity_threshold for x in deduped):
                deduped.append(item)
        selected = _tournament(deduped, cfg)
    frontier = pareto_frontier(selected)[:cfg.pareto_limit]
    return HypothesisRun(
        run_id=_id("hypothesis-run", *(sorted(g.gap_id for g in gaps)), cfg.model_dump_json(sort_keys=True)),
        input_gap_ids=sorted(g.gap_id for g in gaps), generated_count=len(generated), reflected_count=len(generated),
        selected_count=len(selected), pareto_count=len(frontier), candidates=generated,
        pareto_frontier_ids=[x.hypothesis.hypothesis_id for x in frontier],
        selected_hypothesis_ids=[x.hypothesis.hypothesis_id for x in selected[:cfg.keep_diverse_limit]], warnings=[] if generated else ["No eligible verified gaps produced hypotheses."],
    )
