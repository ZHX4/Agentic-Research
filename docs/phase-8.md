# Phase 8 — Evaluation and Benchmarking

Phase 8 evaluates the system without allowing benchmark results to change the scientific artifacts being evaluated. Benchmarks consume frozen inputs and produce immutable result artifacts.

## Evaluation layers

```text
Frozen benchmark cases
        ↓
┌────────────────────────────────────────────────────────┐
│ retrieval      extraction      gap      novelty       │
│ temporal       human          baseline  ablation      │
└────────────────────────────────────────────────────────┘
        ↓
Metric calculations + confidence intervals
        ↓
Cost / compute accounting
        ↓
Composite EvaluationReport
```

## Retrieval benchmark

Measures precision@k, recall@k, F1@k, MRR, MAP@k, and nDCG@k. Expected relevant IDs are fixed in the benchmark case and predictions are evaluated by case ID.

## Extraction benchmark

Measures exact structured-field match and macro field F1 against frozen expected fields. Missing predictions are represented explicitly rather than silently removed from evaluation.

## Gap and novelty benchmarks

Gap and novelty outputs are evaluated as classification labels. Binary precision, recall, F1, and accuracy are available when a positive class is supplied; otherwise exact-label accuracy is reported for the declared benchmark labels.

## Temporal benchmark

Temporal evaluation is isolated from ordinary test evaluation. Every temporal case must declare a cutoff year. Future publication years are leakage and unknown years are reported separately rather than treated as safe historical evidence.

The benchmark reports:

- leakage rate;
- unknown-year rate;
- affected cases.

A temporal benchmark is not allowed to silently mix future and historical information.

## Human evaluation

Human evaluation requires at least two annotators and at least two ratings per evaluated item. Nominal agreement is reported with pairwise Cohen's kappa and Krippendorff alpha. Numeric human scores are aggregated separately.

## Baselines

Baseline comparison requires a common metric across all systems and an explicit higher-is-better/lower-is-better direction. Oracle baselines require documentation of their information access so they cannot be presented as fair competitors by accident.

## Ablations

Ablation artifacts identify the removed component, matched case IDs, baseline metrics, ablated metrics, absolute deltas, and relative deltas. The evaluator does not infer causality merely from a delta; the design must remain matched.

## Cost / compute accounting

Costs record wall time, optional CPU/GPU time, peak memory, token counts, and estimated USD cost. Totals and means are reported without pretending that cost is a scientific quality metric.

## Confidence intervals

Deterministic bootstrap confidence intervals are available for metric means. The random state is an explicit parameter so repeated evaluations can be reproduced.

## Composite reports

`EvaluationReport` combines benchmark, human, baseline, ablation, and cost artifacts. Its report ID is content-derived from the included artifact IDs.

## CLI

```bash
agentic-research-evaluation retrieval \
  --cases benchmarks/retrieval.test.json \
  --predictions artifacts/retrieval.json \
  --system-name agentic-research \
  --output artifacts/evaluation/retrieval.json

agentic-research-evaluation temporal \
  --cases benchmarks/temporal.test.json \
  --predictions artifacts/temporal.json \
  --system-name agentic-research \
  --output artifacts/evaluation/temporal.json

agentic-research-evaluation report \
  --system-name agentic-research \
  --benchmark artifacts/evaluation/retrieval.json \
  --benchmark artifacts/evaluation/temporal.json \
  --output artifacts/evaluation/report.json
```

## Scientific boundary

Phase 8 evaluates the system. It does not:

- generate new research gaps;
- generate hypotheses;
- execute experiments;
- make global novelty claims;
- run autonomous research loops.

Those are earlier or later phase responsibilities.
