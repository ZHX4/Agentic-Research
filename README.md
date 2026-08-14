# Agentic-Research

> **An evidence-grounded autonomous AI research platform for discovering, validating, testing, and packaging scientific knowledge.**

[![CI](https://github.com/ZHX4/Agentic-Research/actions/workflows/ci.yml/badge.svg)](https://github.com/ZHX4/Agentic-Research/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Agentic-Research is a modular, end-to-end research agent designed to help turn scientific literature into **defensible research opportunities and reproducible experimental results**.

Rather than stopping at search, summarization, or one-shot idea generation, the system follows a complete research workflow: it builds structured scientific knowledge from literature, identifies potential gaps, challenges those gaps against prior work, develops falsifiable hypotheses, executes controlled experiments, evaluates the evidence, manages bounded autonomous research loops, and prepares validated outputs for publication.

The project is built around a simple principle:

> **AI-assisted scientific discovery should be evidence-driven, reproducible, traceable, and scientifically accountable.**

---

## Why Agentic-Research?

Scientific knowledge is growing faster than a researcher can reasonably inspect by hand. Important evidence may be distributed across papers, sections, tables, citations, supplementary material, and different terminology for essentially related ideas.

At the same time, modern language models make it easy to generate ideas that *sound* novel without establishing that they are actually new, useful, reproducible, or experimentally supported.

Agentic-Research treats this as an **infrastructure problem rather than a prompting problem**.

The goal is to create an AI research collaborator that can:

- build structured understanding from scientific literature;
- connect papers, methods, datasets, tasks, claims, limitations, and evidence;
- surface promising research opportunities;
- aggressively challenge proposed gaps against prior work;
- generate diverse, explicit, falsifiable hypotheses;
- execute experiments in controlled and reproducible environments;
- evaluate results with benchmark, temporal, human, baseline, and ablation safeguards;
- continue research through bounded autonomous cycles; and
- preserve the evidence needed to package validated work for publication.

Agentic-Research is designed to **augment researchers, not replace them**. Scientific interpretation, domain expertise, and final publication decisions remain human responsibilities.

---

## What It Does

At a high level, Agentic-Research turns a scientific question or literature corpus into a chain of auditable research artifacts:

```text
Scientific literature
        │
        ▼
Literature intelligence
        │
        ▼
Structured scientific knowledge
        │
        ▼
Research opportunity discovery
        │
        ▼
Adversarial novelty verification
        │
        ▼
Falsifiable hypothesis generation
        │
        ▼
Experiment planning and execution
        │
        ▼
Evaluation and validation
        │
        ▼
Bounded autonomous research loop
        │
        ▼
Publication and reproducibility package
```

Every major transition is represented by explicit schemas and persisted artifacts instead of hidden conversational state.

---

## Architecture

Agentic-Research is deliberately modular. Each subsystem owns a well-defined responsibility and communicates through typed contracts, provenance, and durable artifacts.

### 1. Literature Intelligence

The literature layer provides the foundation for scientific discovery:

- source adapters and transport;
- paper identity normalization;
- deduplication;
- metadata handling;
- full-text acquisition;
- structured document processing.

The result is a stable, machine-readable representation of the scientific corpus.

### 2. Scientific Understanding

Scientific documents are transformed into structured evidence, including:

- sections and chunks;
- tables and figures;
- claims and supporting evidence;
- citations;
- methods;
- datasets;
- tasks;
- limitations and contributions.

This allows later components to reason over scientific structure instead of repeatedly treating papers as unstructured text.

### 3. Scientific World Model

The world model connects papers and scientific entities into a persistent representation.

It can represent relationships such as:

```text
Paper ──uses──> Method
Paper ──evaluates──> Dataset
Method ──targets──> Task
Paper ──supports──> Claim
Paper ──cites──> Paper
Claim ──has evidence──> Evidence
```

This representation becomes the foundation for retrieval, comparison, and gap discovery.

### 4. Research Opportunity Discovery

The discovery engine searches for multiple kinds of research opportunities, including:

- missing combinations;
- recurring limitations;
- contradictions;
- underexplored conditions;
- cross-domain connections;
- structural gaps in the scientific graph.

The important distinction is that the system produces **candidate opportunities**, not automatic claims of absolute novelty.

### 5. Adversarial Novelty Verification

A proposed research gap is actively challenged before being promoted.

Verification can combine:

- lexical and semantic retrieval;
- search-probe expansion;
- near-neighbor analysis;
- direct prior-work detection;
- temporal cutoffs;
- counterevidence;
- full-text verification;
- method/dataset/task relationship checks;
- provenance and evidence tracking.

A central integrity rule is enforced throughout the system:

> **Failure to find prior work within a bounded search process is not proof of global novelty.**

Uncertainty therefore remains explicit rather than being converted into unsupported confidence.

### 6. Hypothesis Reasoning

Surviving research opportunities are transformed into candidate hypotheses through multiple complementary strategies.

The reasoning layer supports:

- diverse generation;
- structured reflection;
- hidden-assumption analysis;
- confounder detection;
- failure-mode analysis;
- similarity filtering;
- clustering;
- tournament selection;
- Pareto selection;
- bounded evolution.

Every hypothesis carries an explicit **falsification condition**.

### 7. Scientific Execution

Selected hypotheses become executable experiment specifications.

The execution layer is designed for reproducibility and controlled failure handling. It supports:

- dataset manifests;
- code integrity checks;
- deterministic hashes;
- restricted Docker execution;
- CPU, memory, PID, and timeout limits;
- multi-seed runs;
- metric validation;
- stdout/stderr capture;
- artifact collection;
- environment fingerprints;
- explicit falsification decisions.

A missing or malformed required metric is treated as an invalid scientific execution result rather than silently accepted as success.

### 8. Evaluation and Benchmarking

The evaluation layer provides rigorous measurement for the research system itself.

It covers:

- retrieval quality;
- extraction quality;
- gap and novelty classification;
- temporal leakage;
- human evaluation;
- baseline comparison;
- ablation analysis;
- cost and compute accounting;
- deterministic confidence intervals;
- composite evaluation reports.

Benchmark contamination is explicitly checked using case identifiers and input hashes, while prediction coverage rules prevent malformed evaluation inputs from silently passing.

### 9. Autonomous Research Control

The autonomy layer coordinates research loops without duplicating the underlying scientific logic.

It provides:

- durable SQLite state;
- checkpoints;
- artifact integrity verification;
- resume semantics;
- bounded iterations;
- bounded retries;
- no-progress detection;
- stage-specific reviews;
- independent reviewer responsibilities;
- critical-stop policies;
- provenance harvesting;
- deterministic run reports.

Production integrations use explicit adapters for the underlying scientific services, while lightweight identity adapters are restricted to controlled smoke-test scenarios.

### 10. Publication and Reproducibility Packaging

Validated research outputs can be assembled into release-oriented artifacts such as:

- system manuscripts;
- benchmark papers;
- validated discovery case studies;
- reproducibility packages;
- model and provider disclosures;
- licensing audits;
- publication-readiness reports.

Publication packaging is evidence-gated. The system does not invent missing results, silently ignore missing provenance, or mark incomplete artifacts as publication-ready.

---

## Design Principles

### Evidence before conclusions

Important decisions should be backed by inspectable evidence and provenance instead of unsupported model output.

### Reproducibility by construction

Code, datasets, configuration, environments, seeds, metrics, and artifacts are treated as first-class research objects.

### Fail closed

Missing evidence should result in `blocked` or `inconclusive`, not an optimistic result.

### Bounded autonomy

Autonomous behavior is constrained by iteration budgets, retry limits, resource controls, checkpoints, and review policies.

### Explicit contracts

Subsystems communicate through typed schemas and persisted artifacts rather than implicit assumptions.

### Deterministic artifacts

Stable identifiers, content-addressed artifacts, hashes, and provenance make research runs easier to compare and audit.

### Human scientific oversight

The system accelerates research work while leaving scientific interpretation, domain judgment, and publication decisions under human control.

---

## Key Capabilities

| Capability | What it provides |
| --- | --- |
| Literature intelligence | Structured scientific corpus acquisition and processing |
| Knowledge representation | Persistent relationships across papers and research entities |
| Gap discovery | Multiple signals for finding research opportunities |
| Novelty verification | Adversarial search and evidence-based prior-work checking |
| Hypothesis reasoning | Diverse, reflective, falsifiable research hypotheses |
| Experimentation | Reproducible sandboxed scientific execution |
| Evaluation | Benchmarks, baselines, ablations, human assessment, and temporal safeguards |
| Autonomous control | Durable, bounded research loops with reviewers and resume support |
| Publication packaging | Evidence-gated manuscripts and reproducibility artifacts |

---

## Quick Start

### Requirements

- Python 3.11+
- Git
- Docker for sandboxed experiment execution

### Installation

```bash
git clone https://github.com/ZHX4/Agentic-Research.git
cd Agentic-Research

python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows PowerShell
# .venv\\Scripts\\Activate.ps1

python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Optional embedding support:

```bash
pip install -e ".[embeddings]"
```

All optional project dependencies:

```bash
pip install -e ".[all]"
```

### Environment

Copy `.env.example` to a local `.env` when provider credentials or deployment-specific settings are required.

```bash
cp .env.example .env
```

Never commit real credentials or private datasets.

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

## Typical Workflows

### Discover and challenge a research opportunity

Start with a structured research corpus and identify a candidate opportunity. Then run adversarial verification before investing in experimentation.

```bash
agentic-research-verify --help
```

Inspect the resulting evidence, prior-work matches, temporal coverage, counterevidence, and verification status.

### Turn a verified opportunity into hypotheses

```bash
agentic-research-hypotheses --help
```

The generated artifact contains hypotheses, reflections, diversity information, selection results, and lineage.

### Run a reproducible experiment

```bash
agentic-research-execution --help
```

Experiments are executed within configured resource boundaries and produce structured metrics and artifacts suitable for downstream evaluation.

### Evaluate results

```bash
agentic-research-evaluation --help
```

Use the evaluation layer to compare system behavior, baselines, ablations, temporal integrity, human ratings, and resource costs.

### Run autonomous research control

```bash
agentic-research-autonomous --help
```

Production runs use explicit subsystem adapters, durable state, checkpoints, and review policies so research can continue without relying on one in-memory agent session.

### Prepare a publication package

```bash
agentic-research-publication --help
```

The publication layer verifies evidence, reproducibility artifacts, disclosures, and licensing before marking a bundle ready.

---

## Extensibility

Agentic-Research is designed so that major components can be replaced without rebuilding the entire system.

Possible customization points include:

- literature providers;
- retrieval backends;
- embedding models;
- rerankers;
- language-model providers;
- hypothesis-generation strategies;
- experiment runners;
- benchmark evaluators;
- reviewer implementations.

Integrations should preserve the canonical contracts, deterministic identifiers, provenance references, and integrity checks expected by downstream components.

---

## Configuration

Project defaults live in [`configs/default.yaml`](configs/default.yaml). Environment-specific values belong in `.env`.

Common configuration areas include:

- literature source and transport settings;
- retrieval and reranking parameters;
- search and verification budgets;
- full-text verification limits;
- hypothesis generation and evolution limits;
- experiment timeout and resource controls;
- evaluation settings and benchmark safeguards;
- autonomous retry and iteration policies;
- publication and licensing metadata.

The provider layer is intentionally decoupled from the scientific contracts, allowing infrastructure to be adapted to different environments and model providers.

---

## Technology Stack

### Runtime

- **Python 3.11+**
- **Pydantic 2** for strict contracts and validation
- **Typer** for command-line interfaces
- **SQLite** for durable autonomous state
- **HTTPX** for external HTTP transport
- **Beautiful Soup 4** for HTML parsing
- **PyMuPDF** for PDF processing
- **Rich** for terminal output

### Scientific infrastructure

- hybrid and structured retrieval;
- scientific graph and vector representations;
- Docker-based execution sandboxing;
- multi-seed experiment execution;
- benchmark and human-evaluation tooling.

### Engineering

- **Hatchling** for packaging
- **Pytest** for testing
- **Ruff** for linting and formatting
- **Mypy** for static type checking
- **GitHub Actions** for repository quality automation
- **Dependabot** for dependency update proposals

---

## Repository Layout

```text
Agentic-Research/
├── .github/
│   ├── dependabot.yml
│   └── workflows/
├── configs/
│   └── default.yaml
├── data/
│   └── demo/
├── docs/
├── src/
│   └── agentic_research/
│       ├── literature/
│       ├── intelligence/
│       ├── retrieval/
│       ├── world_model/
│       ├── gaps/
│       ├── verification/
│       ├── hypotheses/
│       ├── execution/
│       ├── evaluation/
│       ├── autonomy/
│       ├── publication/
│       ├── schemas/
│       └── agents/
├── tests/
├── .env.example
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── SECURITY.md
├── pyproject.toml
└── README.md
```

The detailed internal implementation remains in [`docs/`](docs/), keeping this README focused on the product, architecture, and user-facing workflow.

---

## Reproducibility and Scientific Integrity

Agentic-Research treats research provenance as a first-class concern.

Major artifacts can retain or derive:

- paper and source identities;
- evidence references;
- verification decisions;
- hypothesis lineage;
- dataset manifests;
- source/code/data hashes;
- execution environments;
- random seeds;
- metrics and experiment artifacts;
- evaluation reports;
- publication manifests.

The platform also enforces important safety properties such as:

- bounded novelty search;
- explicit uncertainty states;
- restricted experiment execution;
- benchmark split validation;
- prediction coverage validation;
- release-time artifact re-hashing;
- licensing review;
- publication blocking when required evidence is absent.

These mechanisms are designed to make scientific failure visible rather than silently converting it into confidence.

---

## Development

Run the local quality gate before submitting changes:

```bash
ruff check .
ruff format --check .
mypy src tests
pytest -q
```

Focused tests can be run for individual subsystems as needed:

```bash
pytest -q tests/test_phase8.py
apytest="$(true)"  # remove this line; placeholder only for shell examples
```

The repository's CI workflow is configured around the same quality tools. Actual GitHub Actions execution can depend on the availability of GitHub Actions for the repository account.

---

## Contributing

Contributions are welcome, especially improvements to retrieval, scientific extraction, verification, hypothesis reasoning, experiment execution, evaluation, and research tooling.

Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening a pull request.

In general:

1. Keep changes focused and compatible with existing contracts.
2. Add regression tests for new behavior.
3. Update documentation when interfaces or assumptions change.
4. Run the local quality gate.
5. Explain scientific-integrity implications for changes affecting evidence, novelty, experiments, evaluation, autonomy, or publication.
6. Do not commit secrets, private datasets, or generated research artifacts containing confidential information.

---

## Security

See [`SECURITY.md`](SECURITY.md) for vulnerability-reporting guidance and operational considerations.

Production deployments should use least-privilege credentials, explicit secret management, controlled filesystem mounts, and appropriate isolation for experiment workloads.

---

## License

Agentic-Research is released under the [MIT License](LICENSE).

---

## Project Status

The repository contains the complete research platform and its supporting engineering infrastructure.

The implementation is intentionally modular so that research components can evolve independently as better models, retrieval systems, datasets, benchmarks, and experimental methods become available.

For implementation details, internal contracts, research methodology, and design decisions, see the documentation in [`docs/`](docs/).

---

## Vision

Agentic-Research explores a future in which AI systems can participate meaningfully in scientific discovery without sacrificing rigor.

The long-term vision is not an AI that simply produces more research text. It is an AI system that can **understand evidence, challenge its own assumptions, formulate falsifiable ideas, test them reproducibly, learn from failure, and preserve the chain of evidence needed to support its conclusions**.

In that role, the system becomes a research collaborator: faster at search and iteration, stricter about reproducibility, and complementary to human scientific judgment.

---

## Documentation

- [Architecture](docs/architecture.md)
- [Research Methodology](docs/research-methodology.md)
- [Roadmap](docs/roadmap.md)
- [Project Documentation](docs/)

---

<p align="center">
  <strong>Agentic-Research</strong><br>
  Evidence-grounded autonomous research infrastructure.
</p>
