# sci-bench-peft30-v1 — PEFT scientific-validation benchmark

Status: **CORPUS FROZEN 2026-09-25 / LABELS PENDING**.

- Corpus: `manifest.json` (`status: frozen`, N=30, pre-cutoff 20,
  post-cutoff 10, 14 PDF + 16 metadata-only). Validated with zero
  problems (hash chain + artifact bytes). Collection: 5-query
  arXiv + anonymous-OpenAlex sweep, dedup, manual curation;
  see `scripts/COLLECTION.md`, `scripts/CURATION_LOG.md`.
- Provider snapshots: 10/10 frozen (`snapshots/`); Semantic Scholar
  NOT RUN (429, no key).
- Annotation cases: `cases/peft30-v1-cases.json` (14 probes, labels
  `null`). Double annotation + adjudication NOT STARTED — requires
  two independent human annotators. No labels fabricated.
- System run on PEFT-30: BLOCKED until labels are frozen (§12).

## Purpose

Measure whether Agentic-Research discovers meaningful research
opportunities and verifies novelty on realistic literature — without
retuning the engine to the benchmark. Build the measuring instrument
before improving the thing being measured.

## Scope

- Domain: parameter-efficient fine-tuning (LoRA / adapters /
  prefix-tuning), 2020–2024.
- Target: N=30 papers (~20 pre-cutoff discovery + ~10 post-cutoff
  leakage/recall probes).
- Cutoff: `2022-12-31` (year <= 2022 = discovery; 2023–2024 = probes
  only; unknown-year excluded from historical runs and counted).

## Layout

- `manifest.json` — draft (zeros); frozen version carries real hashes.
- `corpus/` — frozen PDFs/HTML (empty until collection).
- `annotations/` — double-annotation templates (A/B/adjudication).
- `cases/adversarial_cases.json` — probe matrix, expected labels `null`
  until adjudicated.
- `snapshots/` — frozen provider responses (none yet).
- `reports/` — deterministic runner outputs (empty).
- `scripts/COLLECTION.md` + `collection_queries.json` — LIVE INPUT recipe.
- `scripts/freeze.py` — `draft -> frozen` with refusal on mutation.
- `schemas/README.md` — points at `src/agentic_research/benchmarks/`.

## Labeling rules (summary)

Gap: `valid_opportunity | already_addressed | partially_addressed |
ambiguous | unsupported`. Novelty: `direct_prior | near_equivalent |
related_not_disqualifying | no_disqualifying_found |
insufficient_evidence`. Two independent ratings per item + adjudicator;
A/B/dissent preserved; only `final_label` becomes `expected_labels`.
Agreement via existing Phase 8 (Cohen kappa + Krippendorff alpha).

## Metrics

Gap precision / false-positive rate / yield (no recall — the universe
of true gaps is undefined); novelty confusion matrix, direct-match
rate, false-disproof / false-survival rates; retrieval P@k/R@k/MRR;
temporal leakage + unknown-year rates; provenance percentages;
hypothesis seven-dimension checklist (no total score).

## Threshold sweeps

`sweep.py` varies near-match (0.62/0.72/0.82), deep floor
(0.35/0.45/0.55), max deep (3/5/8), dedup (0.75/0.82/0.90),
clustering (0.60/0.70/0.80), underexplored coverage (0.10/0.20/0.30),
entity support (1/2/3). **sensitivity analysis != calibration;
benchmark-specific optimization is prohibited.**

## Reproducibility

Freeze = validate manifest + artifacts, compute SHA-256 chain, write
`manifest.json` + `.sha256`, refuse overwrite. Evaluation consumes
only frozen inputs. Provider snapshots are hash-pinned; live results
never become truth.

## What this can and cannot establish

This benchmark can support a narrow empirical claim about performance
on PEFT-30-v1 (e.g. "precision=X, direct-recall=Y, kappa=W").
It cannot establish global research-discovery capability.
A green suite here is still not scientific validation of autonomous
discovery — that requires independent replication on held-out corpora.
