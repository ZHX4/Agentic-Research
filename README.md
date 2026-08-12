# Agentic-Research

An evidence-grounded research-agent system for scientific literature intelligence, gap discovery, adversarial novelty verification, hypothesis reasoning, reproducible experimental validation, and rigorous evaluation.

> **Status:** Phase 8 implemented. Phases 0–8 are complete; Phase 9 has not started.

## Research objective

> Can an evidence-grounded multi-agent system discover scientifically meaningful research gaps with fewer false positives than simpler LLM/RAG baselines, and can verified gaps produce hypotheses that survive reproducible experiments?

The initial domain is **AI/ML research**, with early emphasis on LLM systems: reasoning, retrieval/RAG, memory, long context, efficiency, evaluation, and tool use.

## Implemented architecture

```text
Literature sources
      ↓
Phase 1 Literature Intelligence
      ↓
Phase 2 Paper Intelligence / Evidence
      ↓
Phase 3 Retrieval + Scientific World Model
      ↓
Phase 4 Gap Discovery
      ↓
Phase 5 Adversarial Novelty Verification
      ↓
Phase 6 Hypothesis Factory
      ↓
Phase 7 Scientific Execution
      ↓
Phase 8 Evaluation
      ├── retrieval / extraction benchmarks
      ├── gap / novelty benchmarks
      ├── temporal leakage benchmark
      ├── human evaluation
      ├── baselines / ablations
      ├── cost / compute accounting
      └── composite EvaluationReport
      ↓
Phase 9 Autonomous Discovery (future)
```

## Phase 8: evaluation

Run a retrieval benchmark:

```bash
agentic-research-evaluation retrieval \
  --cases benchmarks/retrieval.test.json \
  --predictions artifacts/retrieval.json \
  --system-name agentic-research \
  --output artifacts/evaluation/retrieval.json
```

Run the temporal leakage benchmark:

```bash
agentic-research-evaluation temporal \
  --cases benchmarks/temporal.test.json \
  --predictions artifacts/temporal.json \
  --system-name agentic-research \
  --output artifacts/evaluation/temporal.json
```

Build a composite evaluation report:

```bash
agentic-research-evaluation report \
  --system-name agentic-research \
  --benchmark artifacts/evaluation/retrieval.json \
  --benchmark artifacts/evaluation/temporal.json \
  --output artifacts/evaluation/report.json
```

## Phase 8 evaluation guarantees

1. Retrieval uses fixed expected IDs and reports Precision@k, Recall@k, F1@k, MRR, MAP@k, and nDCG@k.
2. Extraction evaluation uses frozen expected fields and reports exact match plus macro field F1.
3. Gap and novelty labels are evaluated against frozen benchmark cases rather than generated self-labels.
4. Temporal evaluation is isolated and reports future-item leakage separately from unknown-year coverage.
5. Human evaluation requires at least two annotators and two ratings per evaluated item.
6. Baseline comparisons require an explicit higher-is-better/lower-is-better metric direction.
7. Oracle baselines must disclose their information access.
8. Ablations preserve matched case IDs and report absolute and relative deltas.
9. Cost accounting records wall time and optional CPU/GPU/memory/token/USD measures.
10. Bootstrap confidence intervals use deterministic seeded resampling.
11. Evaluation reports are content-derived and retain the IDs of their component artifacts.
12. Phase 8 never uses evaluation results to retroactively alter the benchmark cases being evaluated.

## Repository layout

```text
src/agentic_research/
  literature/    source adapters, transport, identity, dedup, full-text
  intelligence/  sections, chunks, tables, figures, claims, evidence, citations
  retrieval/     lexical/dense/hybrid retrieval and reranking
  world_model/   persistent scientific graph and vector store
  gaps/          Phase 4 candidate gap discovery
  verification/ Phase 5 Devil's Advocate and novelty verification
  hypotheses/    Phase 6 generation, reflection, clustering, evolution, selection
  execution/     Phase 7 planner, sandbox, runner, metrics, search tree
  evaluation/   Phase 8 benchmarks, human eval, baselines, ablations, cost accounting
  schemas/       canonical scientific contracts
  agents/        provider-independent agent contracts

docs/            architecture, methodology, phase gates, roadmap
tests/           unit and offline integration tests
configs/         reproducible configuration
data/            deterministic demo data only
```

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'

python -m agentic_research.cli --help
agentic-research-verify --help
agentic-research-hypotheses --help
agentic-research-execution --help
agentic-research-evaluation --help
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
- [ ] Phase 9

## Roadmap

- [x] Phase 0 foundation
- [x] Phase 1 literature intelligence
- [x] Phase 2 evidence-grounded paper intelligence
- [x] Phase 3 retrieval and scientific world model
- [x] Phase 4 gap discovery
- [x] Phase 5 adversarial novelty verification
- [x] Phase 6 hypothesis reasoning
- [x] Phase 7 scientific execution
- [x] Phase 8 evaluation
- [ ] Phase 9 autonomous discovery
- [ ] Phase 10 publication
