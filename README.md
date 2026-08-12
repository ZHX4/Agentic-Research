# Agentic-Research

An evidence-grounded research-agent system for scientific literature intelligence, gap discovery, adversarial novelty verification, hypothesis reasoning, and eventually reproducible experimental validation.

> **Status:** Phase 6 implemented. Phases 0–6 are complete; Phase 7 has not started.

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
      ├── generation
      ├── diversity / clustering
      ├── reflection
      ├── tournament
      ├── evolution
      └── Pareto selection
      ↓
Phase 7 Scientific Execution (future)
```

## Phase 6: hypothesis reasoning

```bash
agentic-research-hypotheses reason \
  --input artifacts/novelty-report.json \
  --output artifacts/hypothesis-run.json
```

Phase 6 creates structured hypotheses from eligible Phase 5 verified gaps. It records upstream gap IDs, mechanism, expected effect, falsification condition, assumptions, predictions, scores, reflection, lineage, and final selection.

The default gate accepts `survived` gaps. `weakened` and `uncertain` inputs require explicit configuration; uncertain inputs are never enabled by default.

## Scientific integrity rules

1. Disproved gaps cannot generate hypotheses.
2. A hypothesis is not treated as experimentally validated.
3. Every hypothesis contains an explicit falsification condition.
4. Generation is separated from reflection and selection.
5. Near-duplicates are removed deterministically.
6. Clustering is deterministic and used for diversity control, not truth judgment.
7. Tournament results are deterministic with explicit tie-breaking.
8. Evolution is bounded and fully serialized in the run artifact.
9. Pareto selection does not imply scientific correctness.
10. No generated code or experiment is executed in Phase 6; execution begins in Phase 7.

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
```

## Phase gates

- [x] [Phase 0](docs/phase-0.md)
- [x] [Phase 1](docs/phase-1.md)
- [x] [Phase 2](docs/phase-2.md)
- [x] [Phase 3](docs/phase-3.md)
- [x] [Phase 4](docs/phase-4.md)
- [x] [Phase 5](docs/phase-5.md)
- [x] [Phase 6](docs/phase-6.md)
- [ ] Phase 7

## Roadmap

- [x] Phase 0 foundation
- [x] Phase 1 literature intelligence
- [x] Phase 2 evidence-grounded paper intelligence
- [x] Phase 3 retrieval and scientific world model
- [x] Phase 4 gap discovery
- [x] Phase 5 adversarial novelty verification
- [x] Phase 6 hypothesis reasoning
- [ ] Phase 7 scientific execution
- [ ] Phase 8 evaluation
- [ ] Phase 9 autonomous discovery
- [ ] Phase 10 publication
