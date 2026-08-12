# Agentic-Research

An evidence-grounded research-agent system for scientific literature intelligence, gap discovery, adversarial novelty verification, hypothesis generation, and eventually reproducible experimental validation.

> **Status:** Phase 3 implemented. Phase 0, Phase 1, Phase 2, and Phase 3 are complete; Phase 4 has not started.

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
Paper Intelligence
  - layout-aware sections
  - section-aware chunks
  - tables / figures
  - structured candidate fields
  - claims / evidence
  - citation edges
  - confidence calibration
      |
      v
Phase 3 Retrieval + World Model
  - FTS5/BM25 lexical retrieval
  - model-isolated dense embeddings
  - RRF hybrid retrieval
  - metadata / temporal filters
  - reranking
  - directional citation traversal
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

## Phase 3: retrieval and scientific world model

First create a Phase 2 paper-intelligence artifact as described in `docs/phase-2.md`, then index it:

```bash
python -m agentic_research.cli index \
  --input artifacts/paper-intelligence.json \
  --database artifacts/world-model.sqlite \
  --embedding hash
```

The hash embedding provider is deterministic and intended for tests/offline development. For real semantic retrieval, install the optional model dependency and select SentenceTransformers:

```bash
pip install -e '.[embeddings]'
python -m agentic_research.cli index \
  --input artifacts/paper-intelligence.json \
  --database artifacts/world-model.sqlite \
  --embedding sentence-transformers \
  --embedding-model sentence-transformers/all-MiniLM-L6-v2
```

Hybrid retrieval combines lexical and dense rankings with Reciprocal Rank Fusion rather than mixing incomparable raw scores:

```bash
python -m agentic_research.cli retrieve \
  "retrieval factual accuracy" \
  --database artifacts/world-model.sqlite \
  --mode hybrid \
  --embedding sentence-transformers \
  --reranker cross-encoder
```

The same command supports deterministic lexical retrieval without embeddings:

```bash
python -m agentic_research.cli retrieve \
  "retrieval factual accuracy" \
  --database artifacts/world-model.sqlite \
  --mode lexical \
  --embedding none \
  --reranker lexical
```

Citation/world-model traversal is directional:

```bash
python -m agentic_research.cli traverse \
  "paper:paper-id" \
  --database artifacts/world-model.sqlite \
  --depth 2 \
  --direction out \
  --edge-type cites
```

## Scientific integrity rules

1. A missing retrieval result is never treated as proof of novelty.
2. Extracted fields are candidate data until later validation.
3. Extracted claims are evidence candidates, not automatically true scientific conclusions.
4. Every extracted claim has an explicit evidence object and source chunk.
5. Confidence is heuristic until calibrated against labeled examples.
6. Historical/temporal benchmarks must enforce strict information cutoffs.
7. LLM self-evaluation is not accepted as sole evidence of novelty.
8. Negative and null results are first-class research artifacts.
9. Hybrid retrieval never combines incomparable lexical and dense raw scores; it uses rank fusion.
10. Vectors from different embedding models are isolated and never compared.
11. Citation targets are never guessed; unresolved citations retain their reference provenance.
12. Phase 3 retrieval results are evidence retrieval, not novelty verification or scientific conclusions.

## Repository layout

```text
src/agentic_research/
  literature/    source adapters, transport, identity, dedup, full-text
  intelligence/  sections, chunks, tables, figures, claims, evidence, citations, calibration
  schemas/       canonical scientific data contracts
  storage/       persistence abstractions
  world_model/   persistent scientific graph + chunk/vector store
  ingestion/     deterministic local corpus ingestion
  retrieval/     provider contracts, embeddings, hybrid retrieval, reranking
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
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'

python -m agentic_research.cli --help
python -m agentic_research.cli demo
python -m agentic_research.cli validate --input data/demo/papers.jsonl
python -m agentic_research.cli gaps --input data/demo/papers.jsonl --output artifacts/demo/gaps.json
```

For model-backed semantic retrieval:

```bash
pip install -e '.[embeddings]'
```

## Phase gates

- [x] [Phase 0 acceptance gate](docs/phase-0.md)
- [x] [Phase 1 acceptance gate](docs/phase-1.md)
- [x] [Phase 2 acceptance gate](docs/phase-2.md)
- [x] [Phase 3 acceptance gate](docs/phase-3.md)
- [ ] Phase 4 acceptance gate

See `docs/phase-3-checklist.md` for the Phase 3 implementation checklist.

## Roadmap

- [x] Phase 0 foundation
- [x] Phase 1 literature intelligence
- [x] Phase 2 evidence-grounded paper intelligence
- [x] Phase 3 retrieval and scientific world model
- [ ] Phase 4 gap discovery
- [ ] Phase 5 adversarial novelty
- [ ] Phase 6 hypothesis reasoning
- [ ] Phase 7 scientific execution
- [ ] Phase 8 evaluation
- [ ] Phase 9 autonomous discovery
- [ ] Phase 10 publication
