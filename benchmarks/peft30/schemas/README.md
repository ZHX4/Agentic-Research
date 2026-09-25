# Schemas (authoritative code, not copies)

The machine-readable contracts live in
`src/agentic_research/benchmarks/` and reuse Phase 8 where possible:

- `manifest.py` — `PaperRecord`, `CorpusManifest`, freeze/validate.
- `annotations.py` — gap/novelty labels, double-annotation trail.
- `snapshots.py` — frozen provider responses.
- `sweep.py` — report-only sensitivity harness.
- `provenance.py` — paper-to-hypothesis join report.
- `hypothesis_dims.py` — seven human-rated dimensions (no total score).
- `runner.py` — adapters into `evaluation/engine.py` + `human.py`.

No parallel schema system: `BenchmarkCase`, `PredictionRecord`,
`HumanRating`, `MetricValue` are imported from `schemas/phase8.py`.
