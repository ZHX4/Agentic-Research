# Agentic-Research

An evidence-grounded research-agent system for scientific literature intelligence, gap discovery, adversarial novelty verification, hypothesis generation, and eventually reproducible experimental validation.

> **Status:** Phase 1 implemented. Phase 0 and Phase 1 are complete; Phase 2 has not started.

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
Literature Intelligence
  - source adapters
  - temporal filtering
  - canonical identity
  - deduplication
  - full-text acquisition
  - PDF/HTML parsing
      |
      v
Hybrid Retrieval (future)
      |
      v
Paper Intelligence ---> Evidence Objects (future)
      |
      v
Scientific World Model (future)
      |
      v
Gap Hunter (future)
      |
      v
Devil's Advocate (future)
      |
      v
Novelty Verification (future)
      |
      v
Hypothesis Factory (future)
      |
      v
Experiment Planner / Sandbox (future)
      |
      v
Independent Review / Paper (future)
```

Phase 1 implements literature acquisition and normalization only. It deliberately stops before semantic retrieval, evidence extraction, graph reasoning, novelty verification, and autonomous experimentation.

## Repository layout

```text
src/agentic_research/
  literature/    source adapters, transport, identity, dedup, full-text
  schemas/       canonical scientific data contracts
  storage/       persistence abstractions
  ingestion/     deterministic local corpus ingestion
  retrieval/     provider-independent retrieval contracts
  gaps/          candidate-gap detection
  agents/        agent contracts
  evaluation/    benchmark and metric contracts
  cli.py         command-line entry point

docs/            architecture, methodology, roadmap, phase gates
tests/           unit and offline integration/smoke tests
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

## Phase 1: live literature search

Set provider credentials in `.env` using `.env.example` as the template.

```bash
python -m agentic_research.cli search "retrieval augmented generation" --limit 20 --temporal-cutoff 2025 --output artifacts/search.json
```

OpenAlex requires its API key for the Works API. Semantic Scholar can be used without a key, although its documentation recommends using an API key and respecting provider rate limits. The adapters use conservative configurable intervals.

## Phase 1: full-text acquisition and parsing

Given a JSONL corpus of canonical `Paper` records:

```bash
python -m agentic_research.cli acquire --input data/demo/papers.jsonl --output artifacts/fulltext/manifests.jsonl --output-dir artifacts/fulltext/files
python -m agentic_research.cli parse --manifest artifacts/fulltext/manifests.jsonl --output artifacts/fulltext/documents.jsonl
```

Acquisition records the source, requested/final URL, media type, byte count, SHA-256, timestamp, and status. Parsing supports PDF and HTML in Phase 1.

## Development checks

```bash
ruff check .
ruff format --check .
mypy src tests
pytest -q
```

## Scientific integrity rules

1. A missing retrieval result is never treated as proof of novelty.
2. Every scientific claim must eventually be traceable to evidence or an experiment artifact.
3. Historical/temporal benchmarks must enforce strict information cutoffs.
4. LLM self-evaluation is not accepted as sole evidence of novelty.
5. Generated code must run inside an isolated sandbox before untrusted execution is enabled.
6. Negative and null results are first-class research artifacts.
7. Provider output is treated as time-varying external data and is not used as a deterministic benchmark fixture.

## Phase gates

- [x] [Phase 0 acceptance gate](docs/phase-0.md)
- [x] [Phase 1 acceptance gate](docs/phase-1.md)
- [ ] Phase 2 acceptance gate

See `docs/phase-1-checklist.md` for the implementation checklist.

## Roadmap

- [x] Phase 0 foundation
- [x] Phase 1 literature intelligence
- [ ] Phase 2 evidence-grounded paper intelligence
- [ ] Phase 3 retrieval and scientific world model
- [ ] Phase 4 gap discovery
- [ ] Phase 5 adversarial novelty
- [ ] Phase 6 hypothesis reasoning
- [ ] Phase 7 scientific execution
- [ ] Phase 8 evaluation
- [ ] Phase 9 autonomous discovery
- [ ] Phase 10 publication
