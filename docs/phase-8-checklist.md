# Phase 8 Acceptance Checklist

- [x] Canonical benchmark case and prediction schemas
- [x] Prediction case-ID coverage and duplicate protection
- [x] Retrieval benchmark: Precision@k, Recall@k, F1@k, MRR, MAP@k, nDCG@k
- [x] Extraction benchmark: exact match and case-level macro field F1
- [x] Gap classification benchmark
- [x] Novelty classification benchmark
- [x] Dedicated temporal benchmark with cutoff enforcement
- [x] Temporal leakage and unknown-year accounting
- [x] Train/dev/test case-ID and input-hash disjointness validation
- [x] Multi-rater human evaluation with duplicate-rating protection
- [x] Cohen's kappa and Krippendorff alpha
- [x] Baseline comparison with explicit metric direction
- [x] Baseline reproducibility contract via executable/configured BaselineSpec; execution delegated to Phase 7 sandbox
- [x] Oracle-baseline disclosure guard
- [x] Ablation comparison and matched-case contract
- [x] Cost/compute accounting
- [x] Deterministic bootstrap confidence intervals
- [x] Composite EvaluationReport artifact
- [x] Stable report/run IDs
- [x] Dedicated evaluation CLI
- [x] Offline regression coverage for identified Phase 8 failure modes
- [x] Documentation and reproducible configuration
- [x] Explicit Phase 8 / Phase 9 boundary

Phase 8 evaluates executed artifacts and benchmark datasets. It does not execute experiments itself, generate hypotheses, claim global novelty, or perform autonomous research loops.
