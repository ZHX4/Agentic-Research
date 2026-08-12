# Agentic-Research

An evidence-grounded research-agent system for scientific literature intelligence, gap discovery, adversarial novelty verification, hypothesis reasoning, and reproducible experimental validation.

> **Status:** Phase 7 implemented. Phases 0–7 are complete; Phase 8 has not started.

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
Phase 7 Scientific Execution
      ├── experiment planning
      ├── falsification planning
      ├── dataset manifests + hashes
      ├── Docker sandbox
      ├── multi-seed execution
      ├── metrics + artifact collection
      └── experiment search tree
      ↓
Phase 8 Evaluation (future)
```

## Phase 7: scientific execution

Plan an experiment from a selected hypothesis:

```bash
agentic-research-execution plan \
  --hypothesis-run artifacts/hypothesis-run.json \
  --hypothesis-id <HYPOTHESIS_ID> \
  --code experiments/run.py \
  --command python \
  --command run.py \
  --primary-metric accuracy \
  --output artifacts/experiment.json
```

Execute the plan in the restricted Docker sandbox:

```bash
agentic-research-execution execute \
  --spec artifacts/experiment.json \
  --code-dir experiments \
  --output-dir artifacts/runs/experiment \
  --result artifacts/results/experiment.json
```

By default, the sandbox disables network access, mounts code and datasets read-only, exposes only `/outputs` as writable, drops Linux capabilities, uses `no-new-privileges`, limits CPU/memory/PIDs, and enforces a timeout.

Experiments should write their metrics to `$AGENTIC_RESEARCH_OUTPUT_DIR/metrics.json` using the documented Phase 7 metric contract.

## Scientific integrity rules

1. Disproved gaps cannot generate hypotheses.
2. Hypotheses are not treated as experimentally validated until Phase 7 evidence exists.
3. Every hypothesis has an explicit falsification condition.
4. Generation is separated from reflection and selection.
5. Every execution checks the planned code SHA-256 before launch.
6. Every local dataset is hash-verified before mounting.
7. Multi-seed results are recorded separately before aggregation.
8. Failed/partial execution is not converted into a scientific conclusion.
9. Falsification is determined only from explicit prespecified criteria.
10. Every artifact, stdout/stderr stream, command, and environment fingerprint is recorded.
11. Sandbox execution is deny-by-default and never receives privileged Docker flags from experiment argv.
12. Phase 7 does not perform autonomous discovery or publication.

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
- [ ] Phase 8

## Roadmap

- [x] Phase 0 foundation
- [x] Phase 1 literature intelligence
- [x] Phase 2 evidence-grounded paper intelligence
- [x] Phase 3 retrieval and scientific world model
- [x] Phase 4 gap discovery
- [x] Phase 5 adversarial novelty verification
- [x] Phase 6 hypothesis reasoning
- [x] Phase 7 scientific execution
- [ ] Phase 8 evaluation
- [ ] Phase 9 autonomous discovery
- [ ] Phase 10 publication
