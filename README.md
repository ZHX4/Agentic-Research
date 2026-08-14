# Agentic-Research

> **Evidence-grounded autonomous research infrastructure for scientific literature intelligence, gap discovery, adversarial novelty verification, hypothesis reasoning, reproducible experimentation, rigorous evaluation, and publication packaging.**

[![CI](https://github.com/ZHX4/Agentic-Research/actions/workflows/ci.yml/badge.svg)](https://github.com/ZHX4/Agentic-Research/actions/workflows/ci.yml)

Agentic-Research is a modular research-agent system designed to take a scientific question or literature corpus through a complete, auditable research workflow. The project combines structured literature intelligence, a persistent scientific world model, gap discovery, adversarial novelty checking, hypothesis generation, sandboxed experimentation, benchmark evaluation, bounded autonomous control, and publication-ready packaging.

The system is designed around an important principle: **failure to find evidence within a bounded search budget is not the same as proving global novelty**. Every stage therefore works with explicit contracts, provenance, deterministic identifiers, persisted artifacts, and validation gates.

---

## Table of Contents

- [Project at a Glance](#project-at-a-glance)
- [Motivation and Goals](#motivation-and-goals)
- [How the System Works](#how-the-system-works)
- [End-to-End Pipeline](#end-to-end-pipeline)
- [Phase-by-Phase Architecture](#phase-by-phase-architecture)
- [Core Components](#core-components)
- [Key Design Principles](#key-design-principles)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Typical Workflows](#typical-workflows)
- [Configuration and Customization](#configuration-and-customization)
- [Technologies and Tooling](#technologies-and-tooling)
- [Repository Structure](#repository-structure)
- [Testing and Quality](#testing-and-quality)
- [Reproducibility and Scientific Integrity](#reproducibility-and-scientific-integrity)
- [Publication Workflow](#publication-workflow)
- [Contributing](#contributing)
- [License](#license)
- [Project Status and Scope](#project-status-and-scope)

---

## Project at a Glance

**Primary objective**

Build a research system that can move from scientific literature to defensible research candidates while preserving enough evidence and provenance for every important decision to be inspected, reproduced, challenged, and eventually packaged for publication.

**Initial research domain**

The project is currently oriented toward AI/ML research, with early emphasis on areas such as:

- reasoning and LLM systems;
- retrieval and RAG;
- memory and long-context methods;
- efficiency and scaling;
- evaluation methodology;
- tool use and agentic systems.

**Core output**

The system does not simply generate text. Its central output is a chain of structured research artifacts:

```text
literature evidence
      ↓
scientific entities + claims
      ↓
world-model representation
      ↓
gap candidates
      ↓
adversarial novelty verification
      ↓
research hypotheses
      ↓
falsifiable experiment plans
      ↓
reproducible execution results
      ↓
benchmark/evaluation evidence
      ↓
bounded autonomous research decisions
      ↓
publication-ready package
```

---

## Motivation and Goals

Scientific literature is now large enough that important research opportunities can be difficult to identify manually. A conventional search-and-summarize workflow also has several weaknesses:

- relevant findings are distributed across papers, sections, tables, citations, and supplementary material;
- similar ideas are described using inconsistent terminology;
- apparent gaps may already have been studied under different wording;
- LLM-generated “novel ideas” can be plausible but unsupported or already known;
- experiments can be difficult to reproduce if code, datasets, seeds, environments, or metrics are not captured precisely;
- publication artifacts often lose the provenance that justified the original claim.

Agentic-Research is intended to address these problems as a **research infrastructure problem**, not just a prompt-engineering problem.

### Project goals

1. Build structured scientific intelligence from literature rather than relying on raw text alone.
2. Represent relationships between papers, methods, datasets, tasks, claims, evidence, and limitations.
3. Discover candidate gaps using multiple complementary signals.
4. Attack those candidates with adversarial novelty verification before calling them promising.
5. Generate diverse, falsifiable hypotheses instead of optimizing for plausible prose.
6. Execute experiments inside bounded, reproducible environments.
7. Evaluate systems with explicit benchmark and contamination controls.
8. Provide a bounded autonomous research loop with durable state and reviewer gates.
9. Preserve enough provenance and release metadata to package validated results for publication.

---

## How the System Works

The architecture is intentionally staged. Each phase has a clear responsibility, an explicit contract, persisted artifacts, and a defined boundary with the next phase.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                         Agentic-Research                              │
├─────────────────────────────────────────────────────────────────────────┤
│  Literature → Intelligence → World Model → Gap Discovery              │
│                                      ↓                                  │
│                         Novelty Verification                            │
│                                      ↓                                  │
│                         Hypothesis Reasoning                            │
│                                      ↓                                  │
│                      Scientific Execution                              │
│                                      ↓                                  │
│                       Evaluation & Benchmarks                           │
│                                      ↓                                  │
│                      Autonomous Research Control                        │
│                                      ↓                                  │
│                        Publication Package                              │
└─────────────────────────────────────────────────────────────────────────┘
```

A key design choice is to keep **scientific reasoning** separate from **orchestration**. Phase 9 can coordinate phases 4–8, but it does not duplicate their scientific logic. Similarly, Phase 10 packages evidence and does not invent scientific results.

---

## End-to-End Pipeline

### 1. Literature acquisition and normalization

The literature layer provides source adapters, transport, identity handling, deduplication, and full-text acquisition. It is responsible for creating stable paper-level inputs for downstream processing.

### 2. Paper intelligence

Documents are transformed into structured scientific information, including sections, chunks, tables, figures, claims, evidence, and citations. This creates a representation that downstream components can inspect without repeatedly parsing raw documents.

### 3. Scientific world model

The world model stores relationships between papers and scientific entities such as methods, datasets, tasks, claims, and evidence. It acts as the persistent representation used by retrieval and gap discovery.

### 4. Gap discovery

Multiple detectors look for patterns such as:

- missing combinations;
- contradictions;
- underexplored conditions;
- recurring limitations;
- cross-domain connections;
- graph negative-space.

The output is a set of **candidate gaps**, not claims of proven novelty.

### 5. Adversarial novelty verification

Each promising gap is actively challenged. Search probes are expanded, prior work is retrieved, close matches are compared, counterevidence is collected, temporal constraints are enforced, and bounded full-text checks can be performed.

The result distinguishes between outcomes such as direct prior work, near prior work, contextual evidence, supported candidates, weakened candidates, and inconclusive searches.

### 6. Hypothesis reasoning

Surviving gaps are converted into diverse hypotheses. The Phase 6 system supports multiple generation strategies, deduplication, clustering, reflection, confounder analysis, tournament selection, Pareto selection, and bounded evolution.

Every hypothesis is required to have a falsification condition.

### 7. Scientific execution

Hypotheses are converted into explicit experiment specifications. Execution is reproducibility-oriented and runs inside a restricted Docker environment with bounded resources and explicit code/data integrity checks.

Multi-seed execution captures metrics, logs, artifacts, hashes, environment fingerprints, and falsification outcomes.

### 8. Evaluation and benchmarking

Phase 8 provides evaluation components for retrieval, extraction, gap/novelty classification, temporal leakage, human assessment, baselines, ablations, and cost/compute accounting.

The evaluation layer also enforces benchmark split integrity and prediction coverage constraints.

### 9. Autonomous research control

Phase 9 provides durable state, checkpoints, bounded retries and iterations, provenance harvesting, stage-specific reviewers, critical-stop policies, and resume support.

Production integrations use explicit stage adapters. Deterministic identity adapters are restricted to smoke-test use.

### 10. Publication packaging

Phase 10 turns validated artifacts into release-oriented packages:

- system paper;
- benchmark paper;
- validated discovery case study;
- reproducibility package;
- model/provider disclosure;
- licensing audit;
- publication-readiness decision.

Publication packaging is evidence-gated and never fabricates missing scientific results.

---

## Phase-by-Phase Architecture

| Phase | Responsibility | Main Output |
| --- | --- | --- |
| 0 | Project foundation | Repository structure, contracts, configuration, quality baseline |
| 1 | Literature intelligence foundation | Acquisition and normalization infrastructure |
| 2 | Scientific document intelligence | Structured paper evidence and claims |
| 3 | Scientific world model | Persistent graph/entity representation |
| 4 | Gap discovery | Corpus-relative candidate gaps |
| 5 | Novelty verification | Adversarial verification reports |
| 6 | Hypothesis reasoning | Falsifiable research hypotheses |
| 7 | Scientific execution | Reproducible experiment results |
| 8 | Evaluation | Benchmark and comparative evaluation reports |
| 9 | Autonomous control | Bounded closed-loop research runs |
| 10 | Publication | Evidence-gated release package |

Detailed phase specifications and acceptance checklists are available under [`docs/`](docs/).

---

## Core Components

### Literature and retrieval

Source adapters, transport, identity normalization, deduplication, full-text acquisition, lexical/dense/hybrid retrieval, and reranking.

### Intelligence layer

Structured extraction and evidence representation for sections, chunks, tables, figures, claims, and citations.

### World model

Persistent scientific graph and vector-oriented representation for relationships among papers and research entities.

### Gap discovery

A multi-detector discovery engine with deterministic run artifacts and provenance tracking.

### Novelty verification

Adversarial search and evidence checks, including bounded external full-text verification and temporal safeguards.

### Hypothesis engine

Diverse hypothesis generation, reflection, clustering, evolution, tournament ranking, and Pareto selection.

### Experimental execution

Explicit experiment planning, dataset manifests, SHA-256 integrity checks, Docker sandboxing, multi-seed execution, metrics ingestion, and falsification decisions.

### Evaluation

Benchmark metrics, temporal integrity, human ratings, baselines, ablations, cost analysis, split validation, and composite reports.

### Autonomous control plane

Durable SQLite state, checkpoints, integrity hashes, bounded loops, reviewer panels, provenance harvesting, and deterministic reporting.

### Publication packaging

Manuscript generation, reproducibility manifests, disclosure artifacts, licensing checks, release-time integrity verification, and readiness gating.

---

## Key Design Principles

### Evidence before conclusions

The system prefers explicit evidence and provenance over unsupported model assertions.

### Candidate-relative novelty

A bounded search can establish that a candidate survived a configured search process; it does not prove that no similar work exists anywhere.

### Reproducibility by construction

Code, data, configuration, environment information, seeds, metrics, and artifacts are treated as first-class research objects.

### Deterministic identifiers and reports

Where possible, identifiers and run reports are derived deterministically from stable inputs so repeated runs can be compared and audited.

### Bounded autonomy

Autonomous behavior is deliberately limited by retries, iterations, resource budgets, checkpoints, and review gates.

### Explicit stage boundaries

Each phase owns a specific responsibility. This reduces duplication, makes failures easier to diagnose, and allows individual stages to be tested independently.

### Fail closed on missing evidence

Publication and verification gates should prefer `blocked` or `inconclusive` over inventing certainty.

---

## Installation

### Requirements

- Python 3.11+
- Git
- Docker for Phase 7 sandboxed execution
- A working filesystem for persisted artifacts and run state

Optional embedding/retrieval functionality can be installed through the project's optional dependencies.

### Clone and install

```bash
git clone https://github.com/ZHX4/Agentic-Research.git
cd Agentic-Research

python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -e '.[dev]'
```

For optional embedding support:

```bash
pip install -e '.[embeddings]'
```

For all optional project dependencies:

```bash
pip install -e '.[all]'
```

### Verify the installation

```bash
agentic-research --help
agentic-research-verify --help
agentic-research-hypotheses --help
agentic-research-execution --help
agentic-research-evaluation --help
agentic-research-autonomous --help
agentic-research-publication --help
```

---

## Quick Start

The project is designed to consume structured artifacts rather than hide the workflow inside one command. A typical progression is:

```text
literature artifacts
    → gap candidates
    → novelty report
    → hypothesis run
    → experiment result
    → evaluation report
    → autonomous run/report
    → publication bundle
```

For the exact command-line options and input contracts, use each command's `--help` output and consult the corresponding phase documentation.

---

## Typical Workflows

### Workflow A — Evaluate candidate gaps

1. Start from a Phase 4 gap artifact.
2. Run Phase 5 adversarial verification.
3. Inspect direct/near prior work, evidence coverage, counterevidence, and temporal constraints.
4. Continue only with candidates that satisfy the configured Phase 5 status policy.

Example:

```bash
agentic-research-verify --help
```

### Workflow B — Generate research hypotheses

Provide a Phase 5 verification report to the Phase 6 reasoning CLI:

```bash
agentic-research-hypotheses --help
```

The resulting artifact contains generated hypotheses, reflections, clustering information, selected hypotheses, Pareto-frontier IDs, and lineage information.

### Workflow C — Plan and run experiments

Use Phase 7 to turn a selected hypothesis into a reproducible experiment plan and execute it inside the configured sandbox:

```bash
agentic-research-execution --help
```

The execution layer should be treated as a scientific measurement system: a missing or invalid `metrics.json` is not considered a successful scientific result.

### Workflow D — Produce an evaluation report

Run the benchmark-specific commands and then build a composite report:

```bash
agentic-research-evaluation --help
```

The evaluation layer can compare retrieval quality, extraction quality, gap/novelty labels, temporal leakage, human ratings, baselines, ablations, and costs.

### Workflow E — Run bounded autonomous research

Production Phase 9 runs use canonical Phase 4–8 stage adapters:

```bash
agentic-research-autonomous --help
```

The autonomous controller persists its state and supports bounded resume behavior rather than relying on an in-memory agent conversation.

### Workflow F — Package a publication release

Phase 10 provides a release-oriented workflow:

```bash
agentic-research-publication --help
```

A publication bundle is only considered `ready` when its required manuscripts contain evidence, reproducibility artifacts are intact, required disclosure exists, and licensing checks pass.

---

## Configuration and Customization

Project defaults live in [`configs/default.yaml`](configs/default.yaml). Phase-specific configuration is intentionally explicit so that important research decisions are inspectable and reproducible.

Typical customization points include:

- literature source and transport configuration;
- temporal cutoffs;
- retrieval and ranking settings;
- gap detector thresholds;
- novelty search budgets and deep-verification limits;
- hypothesis generation and evolution budgets;
- experiment CPU, memory, PID, timeout, and seed limits;
- evaluation thresholds, split settings, and bootstrap parameters;
- autonomous iteration/retry budgets and reviewer policies;
- publication artifact and licensing metadata.

### Environment variables

Use [`.env.example`](.env.example) as the starting point for environment-specific configuration. Keep real credentials out of the repository.

### Provider integration

The project is designed around explicit interfaces rather than a hard-coded single model provider. Integrate external model/search services through the provider and stage contracts, then preserve the resulting configuration and provenance in run artifacts.

---

## Technologies and Tooling

### Core software

- **Python 3.11+** — primary implementation language.
- **Pydantic 2** — strict schemas and cross-stage contracts.
- **Typer** — command-line interfaces.
- **HTTPX** — HTTP transport for external services.
- **Beautiful Soup 4** — HTML/full-text parsing.
- **PyMuPDF** — PDF processing.
- **Rich** — terminal presentation.
- **SQLite** — durable Phase 9 run state.
- **Docker** — restricted Phase 7 experiment execution.
- **Hatchling** — Python packaging/build system.
- **Ruff** — linting and formatting.
- **mypy** — static type checking.
- **pytest** — automated tests.
- **GitHub Actions** — repository quality workflow configuration.

### Optional capabilities

The project also exposes optional embedding support through `sentence-transformers`.

---

## Repository Structure

```text
Agentic-Research/
├── .github/
│   └── workflows/
│       └── ci.yml
├── configs/
│   └── default.yaml
├── data/
│   └── demo/
├── docs/
│   ├── architecture.md
│   ├── research-methodology.md
│   ├── roadmap.md
│   └── phase-*.[md]
├── src/
│   └── agentic_research/
│       ├── agents/
│       ├── autonomy/          # Phase 9
│       ├── evaluation/        # Phase 8
│       ├── execution/         # Phase 7
│       ├── gaps/              # Phase 4
│       ├── hypotheses/        # Phase 6
│       ├── intelligence/      # Paper intelligence
│       ├── ingestion/
│       ├── literature/        # Phase 1
│       ├── publication/       # Phase 10
│       ├── retrieval/
│       ├── schemas/
│       ├── verification/      # Phase 5
│       └── world_model/       # Phase 3
├── tests/
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## Testing and Quality

The repository is configured with a quality workflow that performs:

```bash
ruff check .
ruff format --check .
mypy src tests
pytest -q
```

The test suite includes unit and offline integration coverage for phase-specific contracts, deterministic behavior, validation failures, integrity checks, and CLI surfaces.

GitHub Actions is configured to run these checks on pushes to `main` and on pull requests. The repository's implementation does not treat an unavailable CI execution as evidence of a code failure; local execution of the same commands remains the recommended pre-release gate.

---

## Reproducibility and Scientific Integrity

Agentic-Research is intended to make scientific decisions inspectable.

Important persisted evidence includes:

- source identifiers and provenance references;
- temporal cutoffs and search configuration;
- artifact hashes;
- code and dataset manifests;
- experiment seeds and resource limits;
- execution stdout/stderr and result artifacts;
- benchmark inputs and split identifiers;
- human annotation metadata where applicable;
- autonomous checkpoints and reviewer findings;
- publication manifests, disclosures, and license audits.

The project therefore supports an important distinction:

> **A successful pipeline run is not automatically a successful scientific result.**

Scientific conclusions still require appropriate experimental design, interpretation, statistical reasoning, and human scientific judgment.

---

## Publication Workflow

Phase 10 is designed to package validated research rather than manufacture it.

A typical release package contains:

1. **System paper** — architecture and methodological description.
2. **Benchmark paper** — benchmark design and measured results.
3. **Discovery case study** — provenance-backed chain from verified gap to hypothesis, experiment, and evaluation.
4. **Reproducibility package** — source commit, artifact hashes, environment reference, and reproduction commands.
5. **Model/provider disclosure** — records the model/provider roles involved in generation or analysis.
6. **License audit** — verifies artifact licensing status and flags cases requiring manual review.

Publication status is intentionally gated as `ready` or `blocked`. Missing evidence, disclosure, licensing clearance, or reproducibility artifacts should block the release rather than be silently ignored.

---

## Contributing

Contributions are welcome when they preserve the project's emphasis on explicit contracts, reproducibility, and scientific integrity.

### Recommended contribution process

1. Open an issue describing the problem, scientific rationale, or proposed feature.
2. Keep changes scoped to one phase or one cross-cutting concern where possible.
3. Add or update tests for behavioral changes.
4. Update the relevant phase documentation and acceptance checklist when a contract changes.
5. Preserve deterministic IDs and provenance semantics unless there is a strong reason to change them.
6. Avoid silently changing scientific defaults; make meaningful behavior configurable and documented.
7. Run the local quality gate before submitting a pull request:

```bash
ruff check .
ruff format --check .
mypy src tests
pytest -q
```

### Pull requests

Good pull requests should explain:

- what changed;
- why it changed;
- which phase(s) are affected;
- how the change was tested;
- whether any schema, artifact, or reproducibility contracts changed.

---

## License

No `LICENSE` file is currently present in the repository. Until an explicit project license is added, the repository should be treated as **not explicitly licensed for unrestricted reuse**.

Third-party datasets, papers, models, and generated artifacts may have their own licenses and terms. Phase 10 includes an SPDX-aware audit for publication and release packaging, but an automated audit does not replace venue-specific or legal review.

---

## Project Status and Scope

### Current implementation status

```text
Phase 0   ✅ Foundation
Phase 1   ✅ Literature intelligence
Phase 2   ✅ Scientific document intelligence
Phase 3   ✅ Scientific world model
Phase 4   ✅ Gap discovery
Phase 5   ✅ Adversarial novelty verification
Phase 6   ✅ Hypothesis reasoning
Phase 7   ✅ Scientific execution
Phase 8   ✅ Evaluation and benchmarking
Phase 9   ✅ Autonomous research control
Phase 10  ✅ Publication packaging
```

### What “complete” means here

The repository contains the planned architecture, phase-specific implementations, schemas, command-line interfaces, documentation, regression tests, and release safeguards.

It does **not** mean that the system has already discovered a universally novel scientific result, that every external literature source has been exhausted, or that any generated manuscript is guaranteed to be accepted by a journal or conference. Those are empirical and human-evaluated outcomes, not properties that can be guaranteed by software alone.

---

## Documentation

Start with:

- [`docs/architecture.md`](docs/architecture.md) — system architecture.
- [`docs/research-methodology.md`](docs/research-methodology.md) — research methodology and integrity principles.
- [`docs/roadmap.md`](docs/roadmap.md) — full project roadmap and phase gates.
- [`docs/phase-0.md`](docs/phase-0.md) through [`docs/phase-10.md`](docs/phase-10.md) — phase specifications.
- Corresponding `phase-*-checklist.md` files — acceptance criteria for each phase.

---

**Repository:** https://github.com/ZHX4/Agentic-Research
