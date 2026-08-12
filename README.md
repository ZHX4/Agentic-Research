# Agentic-Research

An evidence-grounded research-agent system for scientific literature intelligence, gap discovery, adversarial novelty verification, hypothesis generation, and eventually reproducible experimental validation.

> **Status:** Phase 5 implemented. Phase 0, Phase 1, Phase 2, Phase 3, Phase 4, and Phase 5 are complete; Phase 6 has not started.

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
Phase 4 Gap Discovery
  - missing combinations
  - contradictions
  - underexplored conditions
  - recurring limitations
  - cross-domain gaps
  - graph negative-space signals
      |
      v
Phase 5 Adversarial Verification
  - Devil's Advocate
  - query expansion
  - broader literature search
  - nearest-prior-work comparison
  - counterevidence registry
  - novelty uncertainty
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

## Phase 5: adversarial novelty verification

Verify Phase 4 candidates against the local indexed world model and configured scholarly providers:

```bash
agentic-research-verify verify-gaps \
  --input artifacts/gap-discovery.json \
  --output artifacts/novelty-report.json \
  --database artifacts/world-model.sqlite
```

For a deterministic local-only verification:

```bash
agentic-research-verify verify-gaps \
  --input artifacts/gap-discovery.json \
  --output artifacts/novelty-report.json \
  --database artifacts/world-model.sqlite \
  --no-external
```

Phase 5 distinguishes `disproved`, `weakened`, `supported`, and `inconclusive`. `supported` means the candidate survived the configured verification budget; it does **not** mean globally proven novel.

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
12. Phase 4 candidates are corpus-relative structural signals, not novelty claims.
13. Phase 5 treats failed or empty search as uncertainty, never proof of novelty.
14. Temporal cutoffs exclude future papers and unknown-year papers during historical verification.
15. Phase 5 transitions are reversible only through explicit later research-state logic; no hypothesis generation occurs here.

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
  gaps/          deterministic candidate-gap discovery
  verification/  Devil's Advocate + adversarial novelty verification
  agents/        agent contracts
  evaluation/    benchmark and metric contracts
  cli.py         Phase 0–4 command-line entry point

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
- [x] [Phase 4 acceptance gate](docs/phase-4.md)
- [x] [Phase 5 acceptance gate](docs/phase-5.md)
- [ ] Phase 6 acceptance gate

See `docs/phase-5-checklist.md` for the Phase 5 implementation checklist.

## Roadmap

- [x] Phase 0 foundation
- [x] Phase 1 literature intelligence
- [x] Phase 2 evidence-grounded paper intelligence
- [x] Phase 3 retrieval and scientific world model
- [x] Phase 4 gap discovery
- [x] Phase 5 adversarial novelty verification
- [ ] Phase 6 hypothesis reasoning
- [ ] Phase 7 scientific execution
- [ ] Phase 8 evaluation
- [ ] Phase 9 autonomous discovery
- [ ] Phase 10 publication
