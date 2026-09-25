# Frozen benchmark cases (definitions — expected labels TBD)

Status: **NOT YET FROZEN**. `adversarial_cases.json` defines the probe
matrix (categories A–H from the audit). `expected_label` is `null`
until the double-annotation workflow completes; frozen `cases/*.json`
with adjudicated `expected_labels` are the only evaluation truth.

Categories:

- A gap_discovery: missing-combination probes (incl. sparsity traps).
- B novelty_verification: renamed equivalents, indirect priors.
- C false_disproof: same-family materially-different configs.
- D retrieval: closed-corpus P@k/R@k/MRR probes.
- E temporal_leakage: post-2022 + unknown-year handling.
- F missing_fulltext: metadata-only, unparsable PDF.
- G contradictions: lexically opposed, conditionally compatible.
- H entity_normalization: abbreviations, hyphens, versions, renames.

Rule: expected answers come from the annotation record, never from
copying the implementation's own output.
