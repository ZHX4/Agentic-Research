# Agentic-Research

An evidence-grounded research-agent system for scientific literature intelligence, gap discovery, adversarial novelty verification, hypothesis reasoning, reproducible experimental validation, rigorous evaluation, bounded autonomous research control, and publication packaging.

> **Status:** Phases 0–10 are implemented. Phase 10 provides publication-focused release packaging; publication of a real scientific paper still requires actual research artifacts, benchmark results, human evaluation where applicable, venue requirements, and manual scientific/editorial review.

## Research objective

> Can an evidence-grounded multi-agent system discover scientifically meaningful research gaps with fewer false positives than simpler LLM/RAG baselines, and can verified gaps produce hypotheses that survive reproducible experiments?

The initial domain is **AI/ML research**, with early emphasis on LLM systems: reasoning, retrieval/RAG, memory, long context, efficiency, evaluation, and tool use.

## Implemented architecture

```text
Literature → Paper Intelligence → World Model → Gap Discovery
        → Adversarial Novelty → Hypothesis Factory
        → Scientific Execution → Evaluation
        → Autonomous Discovery → Publication
```

## Phase 9: autonomous control

```bash
agentic-research-autonomous run \
  --run-id run-001 \
  --input-file artifacts/input.json \
  --output artifacts/phase9-report.json

agentic-research-autonomous resume \
  --run-id run-001 \
  --output artifacts/phase9-report.json
```

Phase 9 provides durable SQLite run state, immutable checkpoint snapshots, SHA-256 integrity checks, bounded retries and iterations, no-progress stopping, independent reviewer panels, provenance harvesting, and deterministic reporting. Production runs inject `StageAdapter` implementations connected to the canonical Phase 4–8 services; deterministic identity adapters are restricted to explicit smoke-test mode.

## Phase 10: publication

```bash
agentic-research-publication manifest \
  --source-commit <commit> \
  --artifacts <path> \
  --kinds result \
  --licenses MIT \
  --output artifacts/publication/repro.json

agentic-research-publication audit-license \
  --manifest-file artifacts/publication/repro.json \
  --output artifacts/publication/license-audit.json

agentic-research-publication write-manuscripts \
  --source-commit <commit> \
  --architecture artifacts/publication/architecture.json \
  --evaluation artifacts/evaluation/report.json \
  --case-study artifacts/publication/case-study.json \
  --output-dir artifacts/publication/manuscripts

agentic-research-publication bundle \
  --source-commit <commit> \
  --architecture artifacts/publication/architecture.json \
  --evaluation artifacts/evaluation/report.json \
  --case-study artifacts/publication/case-study.json \
  --disclosure artifacts/publication/disclosure.json \
  --reproducibility artifacts/publication/repro.json \
  --output artifacts/publication/bundle.json
```

Phase 10 provides evidence-gated manuscript generation, validated discovery case-study packaging, reproducibility manifests, model/provider disclosure, SPDX-aware licensing review, release-time artifact hash verification, and publication-readiness checks.

## Scientific integrity guarantees

1. Phases communicate through explicit schemas and persisted artifacts rather than hidden conversational state.
2. Temporal cutoffs and provenance are preserved through literature, novelty, evaluation, execution, and autonomous stages.
3. Phase 5 does not convert bounded search failure into global novelty.
4. Phase 7 uses reproducible code/dataset manifests, integrity hashes, sandboxing, multi-seed execution, and explicit falsification criteria.
5. Phase 8 enforces benchmark split integrity, prediction coverage, metric direction, human-rating constraints, and deterministic evaluation reports.
6. Phase 9 uses durable state, bounded loops, stage-specific review, critical-stop policy, and tamper-evident checkpoints.
7. Phase 10 never invents scientific results and blocks release when required evidence, disclosure, or licensing checks are missing.

## Repository layout

```text
src/agentic_research/
  literature/    source adapters, transport, identity, dedup, full-text
  intelligence/  sections, chunks, tables, figures, claims, evidence, citations
  retrieval/     lexical/dense/hybrid retrieval and reranking
  world_model/   persistent scientific graph and vector store
  gaps/          Phase 4 gap discovery
  verification/ Phase 5 novelty verification
  hypotheses/    Phase 6 hypothesis reasoning
  execution/    Phase 7 scientific execution
  evaluation/   Phase 8 benchmarks and evaluation
  autonomy/     Phase 9 durable autonomous control
  publication/  Phase 10 publication and release packaging
  schemas/      canonical scientific contracts
  agents/       provider-independent agent contracts

docs/            architecture, phase gates, roadmap
configs/         reproducible configuration
tests/           unit and offline integration tests
data/demo/      small deterministic demo inputs
```

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'

agentic-research --help
agentic-research-verify --help
agentic-research-hypotheses --help
agentic-research-execution --help
agentic-research-evaluation --help
agentic-research-autonomous --help
agentic-research-publication --help
```

## Phase gates

- [x] [Phase 0](docs/phase-0.md)
- [x] [Phase 1](docs/phase-1.md)
- [x] [Phase 2](docs/phase-2.md)
- [x] [Phase 3](docs/phase-3.md)
- [x] [Phase 4](docs/phase-4.md)
- [x] [Phase 5](docs/phase-5.md)
- [x] [Phase 6](docs/phase-6.md)
- [x] [Phase 7](docs/phase-7.md)
- [x] [Phase 8](docs/phase-8.md)
- [x] [Phase 9](docs/phase-9.md)
- [x] [Phase 10](docs/phase-10.md)

## Quality gate

GitHub Actions is configured to run installation, Ruff linting, Ruff formatting checks, mypy, and pytest on pushes to `main` and pull requests. A project release should be considered execution-verified only after those checks have actually run and passed on GitHub.
