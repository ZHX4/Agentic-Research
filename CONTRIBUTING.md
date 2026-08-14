# Contributing to Agentic-Research

Thank you for contributing to Agentic-Research. The project treats scientific correctness, reproducibility, and provenance as first-class engineering requirements.

## Before you start

- Read the relevant phase specification under `docs/`.
- Read `docs/architecture.md` and `docs/research-methodology.md` for cross-phase constraints.
- Avoid bypassing schemas, provenance, integrity checks, or acceptance gates merely to simplify a feature.

## Development workflow

1. Create a focused branch from `main`.
2. Make the smallest coherent change that solves the problem.
3. Add or update regression tests for behavior changes.
4. Update documentation and configuration when interfaces change.
5. Run:

```bash
ruff check .
ruff format --check .
mypy src tests
pytest -q
```

6. Open a pull request with a clear description of the problem, design decision, tests performed, and any scientific-integrity implications.

## Scientific changes

Changes affecting novelty verification, hypothesis selection, experiment execution, evaluation metrics, autonomous review, or publication readiness must include explicit evidence of how the change preserves the relevant phase contract.

Do not turn bounded search failure into claims of global novelty, and do not introduce publication-ready status without the required evidence artifacts.

## Commit and pull request guidance

Prefer focused commits and descriptive messages. Pull requests should explain user-facing behavior and call out any backward-incompatible changes.

## Security and sensitive data

Never commit API keys, credentials, private datasets, private paper collections, or generated research artifacts containing secrets. Use environment variables and local ignored files for sensitive configuration.
