# PEFT-30 collection procedure (sci-bench-peft30-v1)

Status: **NOT YET FROZEN** — live collection has not been run in this
environment (no network / no provider credentials exercised here).
This document is the reproducible procedure. The frozen snapshot
(`manifest.json` with `status: frozen` + hashes) is the benchmark;
this document is only the recipe.

## Domain

Parameter-Efficient Fine-Tuning: LoRA / adapters / prefix-tuning and
closely related PEFT methods, 2020–2024.

## Search queries (exact, run one per provider)

1. `LoRA low-rank adaptation fine-tuning`
2. `adapter tuning AdapterHub bottleneck adapter`
3. `prefix-tuning prompt tuning parameter efficient`
4. `QLoRA quantized LoRA GSM8K`
5. `PEFT translation summarization GLUE SuperGLUE`

Record per query: provider, UTC timestamp, result count, top IDs,
failures/retries, temporal filter applied.

## Providers

- OpenAlex (`api.openalex.org/works`, server date filter +
  client post-filter; API key required by current code).
- Semantic Scholar (`api.semanticscholar.org/graph/v1/paper/search`,
  server `year=` filter + client post-filter).
- arXiv (`export.arxiv.org/api/query`, client-side year filter only).

## Inclusion criteria

- Primary topic is a PEFT method applied to at least one
  dataset + task pair.
- Has a resolvable identifier (arXiv ID and/or DOI).
- Publication year known (unknown-year papers are logged
  separately and excluded from the historical discovery corpus).

## Exclusion criteria

- Pure position papers with no method/dataset/task triple.
- Duplicates (same arXiv ID / DOI, title-normalized match).
- Non-English full text without an English abstract.

## Temporal filtering

- Cutoff: `2022-12-31` (year <= 2022 = discovery corpus).
- 2023–2024 papers: leakage / recall probes only, never discovery input.
- Unknown-year: excluded from historical runs, counted in
  `unknown_year_rate`.

## Deduplication

1. Exact arXiv ID / DOI match.
2. Normalized title match (casefold, punctuation stripped).
3. Keep the record with full text preferred over metadata-only;
   log the merge.

## Full-text acquisition

- Prefer open PDF via arXiv; else HTML; else `metadata-only`
  (recorded explicitly, never silently treated as full text).
- Store under `benchmarks/peft30/corpus/` with SHA-256 in the manifest.
- Paywalled / unparsable papers stay `metadata-only` with reason logged.

## Manual curation

- Target N=30: ~20 pre-cutoff (discovery) + ~10 post-cutoff
  (leakage/recall probes, including renames and near-duplicates).
- A curator reviews the ranked candidate list, enforces the
  inclusion rules, and records every manual include/exclude with
  a one-line reason in the collection log.
- Freeze only after curation; no additions after labeling starts.

## Live vs frozen (do not mix)

- `scripts/collection_queries.json` + this file = LIVE COLLECTION INPUT.
- `manifest.json` (frozen) + `corpus/` + `snapshots/` = FROZEN
  BENCHMARK INPUT. Evaluation consumes only the frozen side.
