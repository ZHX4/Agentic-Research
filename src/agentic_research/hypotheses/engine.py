"""Deterministic Phase 6 hypothesis generation and selection."""
from __future__ import annotations
import hashlib, itertools, json
from agentic_research.schemas.gap import GapCandidate, GapStatus
from agentic_research.schemas.phase6 import Hypothesis, HypothesisCandidate, HypothesisConfig, HypothesisReflection, HypothesisRun
from .diversity import similarity, cluster_hypotheses


def _id(prefix: str, *parts: str) -> str:
    return f"{prefix}:{hashlib.sha256('||'.join(parts).encode()).hexdigest()[:20]}"


def _allowed(gaps: list[GapCandidate], cfg: HypothesisConfig) -> list[GapCandidate]:
    allowed = {GapStatus.SURVIVED}
    if cfg.min_gap_status in {GapStatus.WEAKENED, GapStatus.UNCERTAIN}:
        allowed.add(GapStatus.WEAKENED)
    if cfg.min_gap_status == GapStatus.UNCERTAIN and cfg.allow_uncertain_gaps:
        allowed.add(GapStatus.UNCERTAIN)
    return [g for g in gaps if g.status in allowed]


def _scores(g: GapCandidate) -> tuple[float, float, float, float]:
    status = {GapStatus.SURVIVED: 1.0, GapStatus.WEAKENED: 0.55, GapStatus.UNCERTAIN: 0.35}.get(g.status, 0.0)
    evidence = min(1.0, g.support_count / 5.0)
    novelty = min(1.0, 0.45 + 0.35 * g.confidence + 0.20 * status)
    significance = min(1.0, 0.45 + 0.35 * g.structural_support + 0.20 * evidence)
    coverage = g.coverage_ratio if g.coverage_ratio is not None else 0.5
    feasibility = min(1.0, 0.55 + 0.25 * status + 0.20 * (1.0 - coverage))
    return novelty, evidence, significance, feasibility


def reflect(h: Hypothesis) -> HypothesisReflection:
    weaknesses = ([] if h.feasibility_score >= 0.55 else ["Feasibility is limited."]) + ([] if h.novelty_score >= 0.55 else ["Novelty confidence depends on upstream gap evidence."])
    score = max(0.0, min(1.0, 0.55 + 0.20 * h.evidence_score + 0.15 * h.feasibility_score - 0.08 * len(weaknesses)))
    rec = "advance" if score >= 0.72 and not weaknesses else "revise" if score >= 0.50 else "discard"
    return HypothesisReflection(
        reflection_id=_id("reflect", h.hypothesis_id), hypothesis_id=h.hypothesis_id,
        strengths=["Linked to a verified upstream gap.", "Contains an explicit falsification condition."],
        weaknesses=weaknesses, hidden_assumptions=h.assumptions or ["The proposed mechanism can be isolated from implementation artifacts."],
        confounders=["Dataset and baseline choice may confound effects.", "Hyperparameters and compute budgets may confound comparisons."],
        failure_modes=[h.falsification_condition], score=score, recommendation=rec,
    )


def _build(gap: GapCandidate, origin: str, mechanism: str, effect: str, reject: str, assumptions: list[str], predicted: list[str], ordinal: int) -> HypothesisCandidate:
    n, e, s, f = _scores(gap); m = gap.method or "the target method"; d = gap.dataset or "the target dataset"; t = gap.task or "the target task"
    h = Hypothesis(
        hypothesis_id=_id("hyp", gap.gap_id, origin, str(ordinal), mechanism),
        statement=f"For {t}, applying {m} to {d} will produce the predicted effect under the stated controls.",
        research_question=f"Does {m} produce the predicted effect on {d} for {t} under a controlled protocol?",
        source_gap_ids=[gap.gap_id], source_statuses=[gap.status], origin=origin,
        mechanism=mechanism, expected_effect=effect, falsification_condition=reject,
        assumptions=assumptions, predicted_observations=predicted,
        novelty_score=n, evidence_score=e, significance_score=s, feasibility_score=f,
        diversity_score=1.0, robustness_score=0.55, reflection_score=0.5,
    )
    r = reflect(h); return HypothesisCandidate(hypothesis=h.model_copy(update={"reflection_score": r.score}), reflection=r)


def generate_candidates(gaps: list[GapCandidate], config: HypothesisConfig | None = None) -> list[HypothesisCandidate]:
    cfg = config or HypothesisConfig(); out: list[HypothesisCandidate] = []
    templates = [
        ("gap_direct", "directly test the missing configuration", "a measurable improvement", "reject if no improvement over the strongest baseline", ["The configuration is technically realizable."], ["The effect is stable across seeds."]),
        ("gap_conservative", "isolate the narrowest causal mechanism", "a smaller reproducible attributable effect", "reject if the effect disappears under a matched control", ["Only one causal factor changes."], ["Matched-control results support the mechanism."]),
        ("gap_high_risk", "map interaction or failure-boundary behavior", "an interaction effect or systematic boundary", "reject if the interaction is indistinguishable from controls", ["The interaction can be isolated."], ["The boundary is reproducible."]),
        ("gap_composed", "combine the candidate configuration with an adjacent technique", "an incremental effect beyond both components", "reject if no incremental benefit remains under matched controls", ["The adjacent technique is reproducible."], ["Ablation isolates the candidate contribution."]),
        ("gap_conservative", "replicate under a preregistered protocol", "a reproducible result or tight bound", "reject if the result is not reproducible across matched seeds", ["Primary metrics are fixed before analysis."], ["Replication variance remains within tolerance."]),
    ]
    for gap in sorted(_allowed(gaps, cfg), key=lambda x: x.gap_id):
        for i, tpl in enumerate(templates[:cfg.hypotheses_per_gap]):
            item = _build(gap, *tpl, i)
            if not any(similarity(item.hypothesis.statement, x.hypothesis.statement) >= cfg.dedup_similarity_threshold for x in out):
                item = item.model_copy(update={"hypothesis": item.hypothesis.model_copy(update={"diversity_score": 1.0 if not out else 1.0 - max(similarity(item.hypothesis.statement, x.hypothesis.statement) for x in out)})})
                out.append(item)
    source = [x.hypothesis for x in out if x.reflection.recommendation != "discard"]
    added = 0
    for left, right in itertools.combinations(source, 2):
        if set(left.source_gap_ids) & set(right.source_gap_ids):
            continue
        if added >= cfg.max_composed_pairs:
            break
        gap_ids = sorted(set(left.source_gap_ids + right.source_gap_ids))
        synthetic = GapCandidate(gap_id="::".join(gap_ids), gap_type="cross_domain", statement="composed", confidence=min(left.evidence_score, right.evidence_score), support_count=1, structural_support=0.5, rationale="composed", status=GapStatus.SURVIVED)
        item = _build(synthetic, "gap_composed", f"Combine: {left.mechanism} AND {right.mechanism}", "an incremental interaction effect", "reject if the joint system does not outperform both constituents", sorted(set(left.assumptions + right.assumptions)), ["Interaction survives matched-control analysis."], added)
        h = item.hypothesis.model_copy(update={"source_gap_ids": gap_ids, "source_statuses": sorted(set(left.source_statuses + right.source_statuses), key=lambda x: x.value)})
        item = item.model_copy(update={"hypothesis": h})
        if not any(similarity(h.statement, x.hypothesis.statement) >= cfg.dedup_similarity_threshold for x in out):
            out.append(item); added += 1
    return out


def _dominates(a: Hypothesis, b: Hypothesis) -> bool:
    av = (a.novelty_score, a.significance_score, a.feasibility_score); bv = (b.novelty_score, b.significance_score, b.feasibility_score)
    return all(x >= y for x, y in zip(av, bv)) and any(x > y for x, y in zip(av, bv))


def pareto_frontier(items: list[HypothesisCandidate]) -> list[HypothesisCandidate]:
    return sorted([x for x in items if not any(_dominates(y.hypothesis, x.hypothesis) for y in items if y.hypothesis.hypothesis_id != x.hypothesis.hypothesis_id)], key=lambda x: (-x.hypothesis.composite_score, x.hypothesis.hypothesis_id))


def _evolve(item: HypothesisCandidate, generation: int) -> HypothesisCandidate:
    h = item.hypothesis.model_copy(update={"hypothesis_id": _id("hyp-evolved", item.hypothesis.hypothesis_id, str(generation)), "origin": "evolved", "mechanism": item.hypothesis.mechanism + " Add an explicit matched control.", "falsification_condition": item.hypothesis.falsification_condition + " Also reject if the effect disappears under that control.", "robustness_score": min(1.0, item.hypothesis.robustness_score + 0.08)})
    r = reflect(h); return HypothesisCandidate(hypothesis=h.model_copy(update={"reflection_score": r.score}), reflection=r)


def _tournament(items: list[HypothesisCandidate], cfg: HypothesisConfig) -> list[HypothesisCandidate]:
    pool = sorted(items, key=lambda x: (-x.hypothesis.composite_score, x.hypothesis.hypothesis_id))
    for _ in range(cfg.tournament_rounds):
        pool = [max(group, key=lambda x: (x.hypothesis.composite_score, x.reflection.score, x.hypothesis.hypothesis_id)) for group in (pool[i:i + cfg.tournament_size] for i in range(0, len(pool), cfg.tournament_size)) if group]
    return pool[:cfg.keep_diverse_limit]


def run_hypothesis_reasoning(gaps: list[GapCandidate], config: HypothesisConfig | None = None) -> HypothesisRun:
    cfg = config or HypothesisConfig(); initial = generate_candidates(gaps, cfg); pool = [x for x in initial if x.reflection.recommendation != "discard"]; evolved: list[HypothesisCandidate] = []
    for generation in range(1, cfg.max_evolution_generations + 1):
        new = [_evolve(x, generation) for x in pool[:cfg.evolve_top_k]]; evolved.extend(new); pool = _tournament(pool + new, cfg)
    all_items = {x.hypothesis.hypothesis_id: x for x in initial + evolved}; candidates = list(all_items.values()); clusters = cluster_hypotheses(candidates, cfg.clustering_threshold) if candidates else []; frontier = pareto_frontier(pool)[:cfg.pareto_limit]
    return HypothesisRun(
        run_id=_id("hypothesis-run", *(sorted(g.gap_id for g in gaps)), json.dumps(cfg.model_dump(mode="json"), sort_keys=True)), input_gap_ids=sorted(g.gap_id for g in gaps),
        initial_generated_count=len(initial), evolved_count=len(evolved), generated_count=len(candidates), reflected_count=len(candidates), selected_count=len(pool), pareto_count=len(frontier), cluster_count=len(clusters), candidates=candidates,
        pareto_frontier_ids=[x.hypothesis.hypothesis_id for x in frontier], selected_hypothesis_ids=[x.hypothesis.hypothesis_id for x in pool[:cfg.keep_diverse_limit]], warnings=[] if initial else ["No eligible verified gaps produced hypotheses."],
    )
