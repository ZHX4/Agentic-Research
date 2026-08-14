# Phase 10 — Publication

## Purpose

Phase 10 converts validated research-agent outputs into a provenance-backed publication bundle. It does **not** invent scientific results. Every manuscript section must be traceable to supplied evidence references, and every release artifact must have an integrity hash and licensing decision.

## Deliverables

1. System paper: architecture, scientific safeguards, reproducibility, and limitations.
2. Benchmark paper: frozen evaluation protocol, measured results, and cautious interpretation.
3. Validated discovery case study: gap verification → hypothesis → execution → evaluation with provenance.
4. Reproducibility package: source commit, artifact hashes, environment lock reference, and reproduction commands.
5. Model/provider disclosure: provider, model/revision, role, locality, and usage notes.
6. Licensing audit: SPDX-aware pass/review decisions with no silent assumptions.

## Publication states

`draft` means the artifact exists but is not release-ready. `blocked` means required evidence, disclosure, or licensing review is missing. `ready` means all three manuscripts are evidence-backed, disclosure exists, and every audited artifact passes the configured license policy.

## CLI

```bash
agentic-research-publication manifest \
  --source-commit <commit> \
  --artifacts <path> \
  --kinds result \
  --licenses MIT \
  --output artifacts/publication/repro.json

agentic-research-publication write-manuscripts \
  --source-commit <commit> \
  --architecture artifacts/publication/architecture.json \
  --evaluation artifacts/evaluation/report.json \
  --case-study artifacts/publication/case-study.json \
  --output-dir artifacts/publication/manuscripts

agentic-research-publication audit-license \
  --manifest-file artifacts/publication/repro.json \
  --output artifacts/publication/license-audit.json

agentic-research-publication bundle \
  --source-commit <commit> \
  --architecture artifacts/publication/architecture.json \
  --evaluation artifacts/evaluation/report.json \
  --case-study artifacts/publication/case-study.json \
  --disclosure artifacts/publication/disclosure.json \
  --reproducibility artifacts/publication/repro.json \
  --output artifacts/publication/bundle.json
```

## Scientific safety rules

- A failed or bounded search is never converted into a claim of global novelty.
- Publication-ready manuscripts require evidence references.
- A missing SPDX identifier produces `review`, not `pass`.
- Only the configured permissive SPDX allowlist receives automatic `pass`; all other identifiers require manual compatibility review.
- The case study must contain verification, hypothesis, execution, and evaluation records.
- The release bundle records the exact source commit and artifact hashes used to build it.
