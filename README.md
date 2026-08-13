# Agentic-Research

An evidence-grounded research-agent system for scientific literature intelligence, gap discovery, adversarial novelty verification, hypothesis reasoning, reproducible experimental validation, rigorous evaluation, and bounded autonomous research control.

> **Status:** Phase 9 implemented. Phases 0–9 are complete; Phase 10 remains publication-focused.

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

Phase 9 provides durable SQLite run state, immutable checkpoint snapshots, SHA-256 integrity checks, bounded retries and iterations, no-progress stopping, independent reviewer panels, provenance harvesting, and deterministic reporting.

The bundled CLI uses deterministic identity adapters as a control-plane smoke path. Production runs inject `StageAdapter` implementations connected to the canonical Phase 4–8 services.

## Scientific integrity guarantees

1. Phase 9 does not duplicate the scientific logic of Phases 4–8.
2. Run state and checkpoint snapshots are tamper-evident.
3. Iterations, retries, and no-progress loops are bounded.
4. Critical reviewer findings can stop a run.
5. Stage outputs retain hashes and provenance references.
6. Final reports are deterministic from durable state.
7. Phase 9 does not publish or release research artifacts.

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
  execution/     Phase 7 scientific execution
  evaluation/   Phase 8 benchmarks and evaluation
  autonomy/      Phase 9 durable autonomous control
  schemas/       canonical scientific contracts
  agents/        provider-independent agent contracts

docs/            architecture, phase gates, roadmap
configs/         reproducible configuration
tests/           unit and offline integration tests
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
- [ ] Phase 10
