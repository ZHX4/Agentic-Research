# Phase 6 — Hypothesis Reasoning

Phase 6 converts adversarially verified Phase 5 gaps into structured, falsifiable research hypotheses. It does not execute experiments and does not claim that a hypothesis is true.

## Pipeline

```text
Phase 5 verified gap
      ↓
Hypothesis Factory
      ↓
Diversity filtering / clustering
      ↓
Structured reflection
      ↓
Tournament ranking
      ↓
Evolution / revision
      ↓
Pareto frontier
      ↓
Selected hypotheses
```

## Inputs

Only Phase 5 candidates with an allowed status are eligible by default. `survived` is the default minimum; `weakened` may be enabled explicitly; `uncertain` is opt-in and never enabled by default.

## Hypothesis object

Every hypothesis stores:

- source gap IDs and statuses;
- research question;
- mechanism;
- expected effect;
- explicit falsification condition;
- assumptions;
- predicted observations;
- novelty/evidence/significance/feasibility/diversity/robustness/reflection scores;
- origin (`gap_direct`, `gap_conservative`, `gap_high_risk`, `gap_composed`, or `evolved`).

## Generation

The deterministic factory intentionally produces multiple research styles rather than one prompt-derived answer:

1. direct test of the missing configuration;
2. conservative mechanism isolation;
3. high-risk interaction/failure-boundary study;
4. composition with an adjacent technique;
5. preregistered replication/bounding study;
6. controlled stress-test across perturbation regimes.

Cross-gap composition is separately bounded by `max_composed_pairs` and cannot combine two hypotheses from the same gap. Same-gap pairs do not consume the composition budget.

## Diversity and clustering

Near-duplicate hypotheses are removed using deterministic token-Jaccard similarity. Remaining hypotheses are clustered using deterministic connected components at `clustering_threshold`. Clustering is descriptive/selection support; it is not a semantic truth judgment.

## Reflection

Every generated hypothesis receives structured criticism covering:

- weaknesses;
- hidden assumptions;
- confounders;
- failure modes;
- a reflection score;
- `advance` / `revise` / `discard` recommendation.

## Tournament and evolution

Tournament ranking is deterministic and tie-broken by reflection score and hypothesis ID. Evolution adds an explicit matched-control constraint and re-runs reflection. A bounded number of generations is used, and evolved hypotheses retain complete upstream lineage.

## Pareto selection

The frontier is computed across novelty, significance, and feasibility. Composite score is used for deterministic ordering inside the frontier, not as proof of scientific merit.

## CLI

```bash
agentic-research-hypotheses reason \
  --input artifacts/novelty-report.json \
  --output artifacts/hypothesis-run.json
```

Useful controls include hypothesis count per gap, pair-composition budget, dedup threshold, tournament size/rounds, Pareto limit, evolution generations, minimum accepted gap status, uncertain-gap opt-in, and clustering threshold.

## Safeguards

1. Disproved gaps cannot generate hypotheses.
2. Uncertain gaps are excluded unless explicitly enabled.
3. Invalid minimum-gap statuses are rejected by configuration validation.
4. No Phase 6 component executes code or experiments.
5. No hypothesis is treated as experimentally validated.
6. Falsification conditions are mandatory fields.
7. Every selected hypothesis retains upstream gap IDs and source statuses.
8. Run IDs are deterministic for the same gaps/configuration.
9. Evolved hypotheses remain serialized in the run artifact.
10. Pareto and selected IDs must refer to serialized candidates.
11. Empty eligible input produces an explicit warning rather than fabricated hypotheses.
12. Composition skips incompatible same-gap pairs without consuming the pair budget.
