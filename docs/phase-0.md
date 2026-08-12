# Phase 0 — Foundation Acceptance Gate

Phase 0 establishes the deterministic, provider-agnostic research-agent foundation. It is intentionally not an autonomous scientist yet.

## Scope

Phase 0 includes:

- canonical scientific schemas
- strict structured agent and retrieval contracts
- deterministic local JSONL ingestion
- JSONL persistence
- deterministic candidate-gap detection
- CLI entry points
- reproducible demo corpus
- scientific-integrity constraints
- unit tests for domain models, contracts, ingestion, storage, provenance, and gap detection
- linting, formatting, type-checking, and test configuration
- architecture, methodology, and roadmap documentation

## Explicit non-goals

The following belong to later phases and must not be represented as implemented in Phase 0:

- OpenAlex / Semantic Scholar / arXiv network adapters
- full-text PDF parsing
- embeddings or vector databases
- scientific knowledge graph persistence
- adversarial gap verification
- novelty verification
- hypothesis generation by an LLM
- autonomous experiment execution
- sandbox execution
- temporal benchmark evaluation

## Acceptance criteria

A Phase 0 checkout is accepted when all of the following are true:

1. `pip install -e .[dev]` succeeds.
2. `python -m agentic_research.cli --help` succeeds.
3. `python -m agentic_research.cli demo` runs without API keys.
4. `python -m agentic_research.cli validate --input data/demo/papers.jsonl` validates the demo corpus.
5. `python -m agentic_research.cli gaps --input data/demo/papers.jsonl --output artifacts/demo/gaps.json` creates deterministic JSON output.
6. `ruff check .` passes.
7. `ruff format --check .` passes.
8. `mypy src tests` passes.
9. `pytest -q` passes.
10. No candidate-gap detector output uses a verified/survived status merely because a corpus lacks a paper.
11. No API keys or secrets are committed.

## Reproducibility rule

A run must be explainable from versioned source, configuration, and input corpus. Later phases add model identifiers, dataset manifests, seeds, and experiment artifacts to this provenance requirement.

## Phase closure

Do not start Phase 1 until this acceptance gate is satisfied in a clean checkout.
