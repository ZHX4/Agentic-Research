# Agentic-Research

An evidence-grounded research agent for scientific gap discovery, adversarial novelty verification, hypothesis generation, and eventually reproducible experimental validation.

> **Status:** Foundation / MVP-0. The repository starts intentionally small and modular. The architecture is designed to evolve into an autonomous research system without coupling the project to a single LLM, search provider, vector database, or orchestration framework.

## Research objective

The core research question is:

> Can an evidence-grounded multi-agent system discover scientifically meaningful research gaps with fewer false positives than simpler LLM/RAG baselines, and can verified gaps produce hypotheses that survive reproducible experiments?

The initial research domain is **AI/ML research**, with early emphasis on **LLM systems** (reasoning, retrieval/RAG, memory, long context, efficiency, evaluation, and tool use).

## Architecture

```text
Research Goal
      |
      v
Literature Planner ---> OpenAlex / Semantic Scholar / arXiv
      |
      v
Hybrid Retrieval (lexical + semantic + citation + metadata)
      |
      v
Paper Intelligence ---> Evidence Objects
      |
      v
Scientific World Model (documents + claims + methods + tasks + datasets + graph)
      |
      v
Gap Hunter
      |
      v
Devil's Advocate ----> Counter-evidence search
      |
      v
Novelty Verification
      |
      v
Hypothesis Factory
      |
      v
Tournament / Evolution
      |
      v
Experiment Planner
      |
      v
Sandboxed Experiment Engine
      |
      +----> Falsification
      |
      v
Independent Review
      |
      v
Traceable Research Report / Paper
```

## Repository layout

```text
src/agentic_research/
  schemas/       canonical scientific data contracts
  storage/       persistence abstractions
  ingestion/     corpus ingestion adapters
  retrieval/     retrieval interfaces
  gaps/          candidate-gap detection
  agents/        agent contracts and orchestration interfaces
  evaluation/    benchmark and metric contracts
  cli.py         command-line entry point

docs/            research and architecture documentation
configs/         reproducible configuration
data/            local demo/processed data (not production corpora)
tests/            unit tests
```

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\\Scripts\\Activate.ps1

python -m pip install --upgrade pip
pip install -e .[dev]

python -m agentic_research.cli --help
python -m agentic_research.cli demo
python -m agentic_research.cli gaps --input data/demo/papers.jsonl --output artifacts/demo/gaps.json
```

The demo pipeline is deterministic and does **not** require API keys.

## Configuration

Copy `.env.example` to `.env` when external providers are added. Never commit credentials.

Configuration is intentionally provider-agnostic. Future providers implement interfaces rather than leaking SDK-specific types through the core domain model.

## Development

```bash
ruff check .
ruff format --check .
pytest -q
```

## Scientific integrity rules

1. A missing retrieval result is never treated as proof of novelty.
2. Every scientific claim must be traceable to evidence or an experiment artifact.
3. Historical/temporal benchmarks must enforce strict information cutoffs.
4. LLM self-evaluation is not accepted as sole evidence of novelty.
5. Generated code must run inside an isolated sandbox before untrusted execution is enabled.
6. Negative and null results are first-class research artifacts.
7. Every research run records its model, configuration, dataset manifest, code revision, and seed.

## Roadmap

- [x] Foundation package and schemas
- [x] Deterministic local corpus ingestion
- [x] First candidate-gap detector
- [x] CLI and developer tooling
- [x] Scientific methodology documentation
- [ ] OpenAlex / Semantic Scholar / arXiv adapters
- [ ] Full-text parsing and evidence extraction
- [ ] Hybrid retrieval
- [ ] Scientific knowledge graph
- [ ] Adversarial gap verification
- [ ] Novelty engine
- [ ] Hypothesis tournament
- [ ] Experiment planner and sandbox
- [ ] Temporal benchmark
- [ ] End-to-end autonomous discovery
