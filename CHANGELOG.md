# Changelog

All notable project changes are documented here.

## [1.1.0] - 2026-08-14

### Added

- Complete Phase 0–10 research pipeline.
- Adversarial novelty verification with bounded deep full-text verification.
- Structured hypothesis generation, reflection, diversity analysis, evolution, tournament ranking, and Pareto selection.
- Sandboxed multi-seed scientific execution with code/data integrity checks.
- Comprehensive evaluation and benchmarking infrastructure.
- Durable autonomous research control with checkpoints, resume support, stage-specific review, and critical-stop policies.
- Evidence-gated publication packaging with reproducibility manifests, disclosure, licensing audits, and release-time artifact verification.
- Production documentation, contribution guidance, security policy, dependency update automation, and explicit MIT licensing.

### Engineering

- Strict Pydantic contracts across phases.
- Dedicated command-line interfaces for verification, hypotheses, execution, evaluation, autonomy, and publication.
- Ruff, mypy, and pytest quality gates.
- GitHub Actions workflow configuration for repository quality checks.

## [1.2.0] - 2026-09-23

### Fixed

- Phase 0–1 ship-blockers: Typer-incompatible CLI option, world-model SQL placeholder mismatch, and missing evaluation report validation.
- Phase 2 paper intelligence: isotonic calibration validator, entity extraction article handling, reference-section boundary, and figure fixture compatibility.
- Phase 3–4 discovery: entity normalization preserving discriminative tokens and resolvable paper-node signal provenance.
- Phase 5 novelty verification: exact-combination disproof independent of title similarity, world-model entity enrichment for local priors, and deep-verification rescue for title-promising metadata-only priors.
- Phase 6 hypothesis diversity: per-strategy effect statements and cross-gap composition accounting.
- Phase 7 experiment planning: duplicate-seed rejection before normalization.
- Phase 8–10: evaluation report validation, autonomous retry error clearing, and publication CLI compatibility with the installed Typer version.
- Literature settings: added missing `fulltext_min_interval_seconds` (previously crashed deep verification at runtime).
- Quality gates: full `ruff check`, `ruff format`, `mypy --strict`, and `pytest` green; offline end-to-end release check in `scripts/e2e_offline.sh`.

### Engineering

- Offline release validation covering literature, intelligence, world model, gaps, verification, hypotheses, planning, evaluation, autonomy smoke control, and publication packaging.

## [Unreleased]

Future changes should preserve the phase contracts, provenance requirements, reproducibility guarantees, and publication-readiness gates documented under `docs/`.
