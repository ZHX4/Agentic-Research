# Agentic-Research

An evidence-grounded research-agent foundation for scientific gap discovery, adversarial novelty verification, hypothesis generation, and eventually reproducible experimental validation.

> **Status:** Phase 0 foundation implemented. Phase 1 has not started. Phase 0 deliberately stops before network retrieval, full-text parsing, novelty verification, and autonomous experiment execution.

## Research objective

The core research question is:

> Can an evidence-grounded multi-agent system discover scientifically meaningful research gaps with fewer false positives than simpler LLM/RAG baselines, and can verified gaps produce hypotheses that survive reproducible experiments?

The initial research domain is **AI/ML research**, with early emphasis on **LLM systems** (reasoning, retrieval/RAG, memory, long context, efficiency, evaluation, and tool use).

## Architecture target

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

Only the foundation through deterministic local candidate-gap discovery is implemented in Phase 0.

## Repository layout

```text
src/agentic_research/
  schemas/       canonical scientific data contracts
  storage/       persistence abstractions
  ingestion/     corpus ingestion adapters
  retrieval/     retrieval interfaces
  gaps/          candidate-gap detection
  agents/        agent contracts
  evaluation/    benchmark and metric contracts
  cli.py         command-line entry point

docs/            architecture, methodology, roadmap, Phase 0 acceptance
tests/           unit and smoke tests
configs/         reproducible configuration
data/            deterministic demo data only
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
python -m agentic_research.cli validate --input data/demo/papers.jsonl
python -m agentic_research.cli gaps --input data/demo/papers.jsonl --output artifacts/demo/gaps.json
```

The demo pipeline is deterministic and does **not** require API keys.

## Development checks

```bash
ruff check .
ruff format --check .
mypy src tests
pytest -q
```

## Scientific integrity rules

1. A missing retrieval result is never treated as proof of novelty.
2. Every scientific claim must be traceable to evidence or an experiment artifact.
3. Historical/temporal benchmarks must enforce strict information cutoffs.
4. LLM self-evaluation is not accepted as sole evidence of novelty.
5. Generated code must run inside an isolated sandbox before untrusted execution is enabled.
6. Negative and null results are first-class research artifacts.
7. Research runs must record configuration, dataset manifests, model identifiers, code revision, and seeds once those providers are enabled.

## Phase 0 acceptance

See [`docs/phase-0.md`](docs/phase-0.md) for the complete acceptance gate and [`docs/phase-0-checklist.md`](docs/phase-0-checklist.md) for the implementation checklist.

## Roadmap

- [x] Phase 0 foundation package and schemas
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
