# Agentic-Research

An evidence-grounded research-agent system for scientific literature intelligence, gap discovery, adversarial novelty verification, hypothesis generation, and eventually reproducible experimental validation.

> **Status:** Phase 2 implemented. Phase 0, Phase 1, and Phase 2 are complete; Phase 3 has not started.

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
Hybrid Retrieval (future)
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

## Phase 2: paper intelligence

Given one canonical `Paper` JSON object and an acquired PDF:

```bash
python -m agentic_research.cli analyze \
  --paper artifacts/paper.json \
  --pdf artifacts/paper.pdf \
  --output artifacts/paper-intelligence.json
```

The resulting `StructuredExtraction` contains sections, chunks, tables, figures, references, citation edges, claims, and explicit claim-to-evidence links. Candidate fields are marked as candidates rather than scientific truth.

### Confidence calibration

Create labeled examples with `raw_confidence` and `correct`, then measure calibration:

```bash
python -m agentic_research.cli calibrate \
  --input artifacts/claim-labels.jsonl \
  --output artifacts/calibration.json
```

The calibration module provides ECE, MCE, Brier score, and a serializable isotonic calibrator. Calibration requires external labels; the system never invents them.

## Repository layout

```text
src/agentic_research/
  literature/    source adapters, transport, identity, dedup, full-text
  intelligence/  sections, chunks, tables, figures, claims, evidence, citations, calibration
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

## Scientific integrity rules

1. A missing retrieval result is never treated as proof of novelty.
2. Extracted fields are candidate data until later validation.
3. Extracted claims are evidence candidates, not automatically true scientific conclusions.
4. Every extracted claim has an explicit evidence object and source chunk.
5. Confidence is heuristic until calibrated against labeled examples.
6. Historical/temporal benchmarks must enforce strict information cutoffs.
7. LLM self-evaluation is not accepted as sole evidence of novelty.
8. Negative and null results are first-class research artifacts.
9. Provider output is time-varying external data and is not used as a deterministic benchmark fixture.

## Phase gates

- [x] [Phase 0 acceptance gate](docs/phase-0.md)
- [x] [Phase 1 acceptance gate](docs/phase-1.md)
- [x] [Phase 2 acceptance gate](docs/phase-2.md)
- [ ] Phase 3 acceptance gate

See `docs/phase-2-checklist.md` for the Phase 2 implementation checklist.

## Roadmap

- [x] Phase 0 foundation
- [x] Phase 1 literature intelligence
- [x] Phase 2 evidence-grounded paper intelligence
- [ ] Phase 3 retrieval and scientific world model
- [ ] Phase 4 gap discovery
- [ ] Phase 5 adversarial novelty
- [ ] Phase 6 hypothesis reasoning
- [ ] Phase 7 scientific execution
- [ ] Phase 8 evaluation
- [ ] Phase 9 autonomous discovery
- [ ] Phase 10 publication
