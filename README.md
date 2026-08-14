# Agentic-Research

> Evidence-grounded autonomous research infrastructure for scientific discovery, from literature intelligence and gap discovery to reproducible experimentation and publication packaging.

[![CI](https://github.com/ZHX4/Agentic-Research/actions/workflows/ci.yml/badge.svg)](https://github.com/ZHX4/Agentic-Research/actions/workflows/ci.yml)

## Overview

Agentic-Research is an end-to-end AI research agent platform designed to support the complete scientific workflow. Instead of producing isolated answers or unsupported research ideas, it builds a structured, auditable pipeline that transforms scientific knowledge into validated research opportunities.

The system combines:

- scientific literature intelligence;
- knowledge representation and world modeling;
- research gap discovery;
- adversarial novelty verification;
- hypothesis generation and ranking;
- reproducible experiment execution;
- rigorous evaluation and benchmarking;
- autonomous research orchestration;
- publication-ready artifact generation.

The core principle of the project is simple:

**AI research assistance should be evidence-driven, reproducible, and scientifically accountable.**

---

## Motivation

Modern scientific literature grows faster than researchers can manually analyze. Important ideas may be hidden across thousands of papers, described using different terminology, or overlooked because connections between methods, datasets, and problems are difficult to track.

Agentic-Research addresses this challenge by building a complete research infrastructure capable of helping researchers:

- understand existing scientific knowledge;
- identify meaningful research opportunities;
- test whether ideas are actually novel;
- design experiments with reproducibility guarantees;
- evaluate results objectively;
- prepare research outputs for publication.

The goal is not to replace researchers, but to create an AI research collaborator that accelerates discovery while preserving scientific standards.

---

# Complete Research Pipeline

```text
Scientific Literature
        ↓
Literature Intelligence
        ↓
Scientific World Model
        ↓
Research Gap Discovery
        ↓
Adversarial Novelty Verification
        ↓
Hypothesis Reasoning
        ↓
Reproducible Experiment Execution
        ↓
Evaluation & Benchmarking
        ↓
Autonomous Research Control
        ↓
Publication Package
```

---

# Architecture

## Phase 0 — Foundation

Creates the repository foundation, development standards, contracts, configuration, and quality infrastructure.

## Phase 1 — Literature Intelligence

Handles scientific source ingestion, normalization, identity management, and literature processing.

## Phase 2 — Scientific Understanding

Extracts structured information such as:

- methods;
- datasets;
- tasks;
- claims;
- evidence;
- limitations.

## Phase 3 — Research Gap Discovery

Finds candidate opportunities through:

- missing combinations;
- limitations;
- contradictions;
- underexplored directions;
- graph-based discovery.

## Phase 4 — Scientific World Model

Builds persistent representations connecting papers, concepts, methods, datasets, and evidence.

## Phase 5 — Novelty Verification

Challenges candidate gaps using adversarial retrieval, prior-work analysis, temporal constraints, and evidence verification.

A candidate surviving verification is not automatically proven novel; it is a research opportunity supported by bounded evidence.

## Phase 6 — Hypothesis Reasoning

Generates and ranks research hypotheses using:

- diverse generation strategies;
- reflection;
- criticism;
- clustering;
- evolution;
- Pareto selection.

## Phase 7 — Scientific Execution

Runs experiments with:

- Docker isolation;
- dataset manifests;
- code integrity checks;
- multi-seed execution;
- artifact tracking;
- reproducible environments.

## Phase 8 — Evaluation

Provides:

- benchmark metrics;
- baseline comparison;
- ablation analysis;
- human evaluation;
- temporal leakage checks;
- cost analysis.

## Phase 9 — Autonomous Research Loop

Provides controlled autonomy with:

- checkpoints;
- resume support;
- bounded iterations;
- reviewer agents;
- provenance tracking;
- scientific integrity gates.

## Phase 10 — Publication

Creates publication-oriented artifacts:

- system manuscripts;
- benchmark reports;
- discovery case studies;
- reproducibility packages;
- disclosure reports;
- licensing audits.

---

# Key Features

## Evidence-Based Research

Every important decision is connected to structured evidence and provenance.

## Reproducibility First

The system tracks:

- code versions;
- datasets;
- configurations;
- environments;
- experiment artifacts;
- hashes.

## Modular Architecture

Each phase has independent contracts, schemas, tests, and outputs.

## Safe Autonomous Operation

Autonomous behavior is controlled through:

- resource limits;
- checkpoints;
- validation gates;
- reviewer policies.

## Publication Readiness

The system does not create publication bundles unless required evidence, artifacts, disclosures, and integrity checks are satisfied.

---

# Installation

## Requirements

- Python 3.11+
- Git
- Docker (required for experiment execution)

## Setup

```bash
git clone https://github.com/ZHX4/Agentic-Research.git
cd Agentic-Research

python -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"
```

Windows:

```powershell
.venv\Scripts\activate
pip install -e ".[dev]"
```

---

# Usage

Available command-line interfaces:

```bash
agentic-research
agentic-research-verify
agentic-research-hypotheses
agentic-research-execution
agentic-research-evaluation
agentic-research-autonomous
agentic-research-publication
```

Use `--help` on each command for available options.

Example workflow:

```text
1. Process literature
2. Discover candidate gaps
3. Verify novelty
4. Generate hypotheses
5. Execute experiments
6. Evaluate results
7. Run autonomous review loop
8. Generate publication package
```

---

# Configuration

Configuration files are located in:

```text
configs/
```

Important configurable areas include:

- model providers;
- retrieval settings;
- search budgets;
- experiment limits;
- evaluation parameters;
- autonomous loop policies;
- publication settings.

Sensitive values should be stored through environment variables and never committed.

---

# Technology Stack

## Core

- Python
- Pydantic
- Typer
- SQLite
- Docker

## Scientific Infrastructure

- Literature retrieval systems
- Document parsers
- Vector and graph representations
- Experiment runners
- Benchmark evaluators

## Development

- Pytest
- Ruff
- Mypy
- GitHub Actions

---

# Repository Structure

```text
Agentic-Research/
│
├── src/
│   └── agentic_research/
│
├── configs/
├── docs/
├── tests/
├── examples/
├── pyproject.toml
└── README.md
```

---

# Development

Run tests:

```bash
pytest
```

Run linting:

```bash
ruff check .
```

Run type checking:

```bash
mypy src tests
```

---

# Contribution Guidelines

Contributions are welcome.

Before submitting changes:

1. Create a feature branch.
2. Add tests for new behavior.
3. Update documentation.
4. Run formatting, linting, and tests.
5. Describe design decisions in the pull request.

---

# License

This project is distributed under the license specified in the `LICENSE` file.

Review the license before using, modifying, or redistributing this project.

---

# Project Status

Current implementation status:

```text
Phase 0  ✅
Phase 1  ✅
Phase 2  ✅
Phase 3  ✅
Phase 4  ✅
Phase 5  ✅
Phase 6  ✅
Phase 7  ✅
Phase 8  ✅
Phase 9  ✅
Phase 10 ✅
```

Agentic-Research is an exploration of how AI systems can become reliable research collaborators by combining automation with evidence, reproducibility, and scientific discipline.
