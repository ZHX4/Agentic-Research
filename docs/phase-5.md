# Phase 5 — Adversarial Novelty Verification

Phase 5 attempts to **disprove** Phase 4 candidate gaps. It performs deterministic query expansion, local-world search, configured external literature search, prior-work comparison, counterevidence registration, and uncertainty reporting.

## Pipeline

```text
Phase 4 candidate
      ↓
Query expansion
      ↓
Local indexed-world search
      ↓
External scholarly search
      ↓
Deduplicate prior work
      ↓
Nearest-prior-work comparison
      ↓
Direct / near / contextual challenge classification
      ↓
Counterevidence registry
      ↓
Coverage assessment
      ↓
Conservative verdict
      ↓
Candidate status transition
```

## Verdict semantics

- `disproved`: a sufficiently similar prior work directly matches the candidate combination.
- `weakened`: close prior work materially challenges the candidate but does not cross the direct-match threshold.
- `supported`: the candidate survived the configured search budget without a direct or near match.
- `inconclusive`: search coverage was insufficient to support or reject the candidate.

`survived` means **survived this configured verification budget**, not globally novel.

## Search strategy

The verifier creates deterministic probes from:

- the original candidate statement;
- normalized statement;
- exact entity combination;
- unquoted entity combination;
- method/dataset;
- method/task;
- dataset/task;
- a small fixed terminology-alias table for common AI abbreviations.

It does not claim that this alias table is exhaustive. Broader search remains subject to the configured providers and budget.

## Prior-work comparison

Each retrieved paper receives interpretable overlap measurements for:

- method overlap;
- dataset overlap;
- task overlap;
- title overlap;
- overall statement/paper token overlap;
- exact candidate-combination match.

This produces `direct`, `near`, or `contextual` prior-work records.

## Counterevidence

Direct and near matches are registered as explicit counterevidence objects with severity. No paper is automatically treated as counterevidence merely because it is superficially related.

## Temporal integrity

When `temporal_cutoff` is set:

- future papers are excluded;
- papers with unknown publication years are excluded;
- local and external searches use the same cutoff contract.

This prevents future-information leakage in historical evaluation.

## Coverage

- `broad`: at least the configured number of successful probes and at least two search sources.
- `moderate`: sufficient successful probes or multiple search sources, but not both broad criteria.
- `limited`: at least one successful search probe.
- `none`: no successful search probe.

Coverage is a search-budget property, not a claim about the completeness of science.

## CLI

Phase 5 uses a separate entry point so the lightweight Phase 0–4 CLI remains stable:

```bash
agentic-research-verify verify-gaps \
  --input artifacts/gap-discovery.json \
  --output artifacts/novelty-report.json \
  --database artifacts/world-model.sqlite
```

External search can be disabled for deterministic local verification:

```bash
agentic-research-verify verify-gaps \
  --input artifacts/gap-discovery.json \
  --output artifacts/novelty-report.json \
  --database artifacts/world-model.sqlite \
  --no-external
```

Or local search can be disabled when only configured external sources are wanted:

```bash
agentic-research-verify verify-gaps \
  --input artifacts/gap-discovery.json \
  --output artifacts/novelty-report.json \
  --no-local
```

## Scientific safeguards

1. Phase 5 accepts only `candidate` inputs from Phase 4.
2. No failed search is interpreted as proof of novelty.
3. Unknown-year papers are excluded from temporal-cutoff evaluations.
4. External provider failures become explicit limitations rather than silent success.
5. `supported` means survived the configured search budget, never “globally proven novel”.
6. Status transitions can be disabled for benchmarking.
7. All probes, prior-work matches, counterevidence, coverage, and limitations are serialized.
8. The verifier is deterministic given the same candidate, configuration, and provider outputs.
9. Phase 5 does not generate research hypotheses or experiments; those begin in Phase 6+.

## Deliberate limitations

- Query expansion is deterministic and intentionally conservative; it is not a complete synonym generator.
- Similarity is interpretable lexical/field overlap rather than a proof of semantic equivalence.
- External-source coverage depends on the configured provider set, API availability, and search limits.
- The verifier cannot establish that no unpublished or inaccessible work exists.
- Contradiction resolution is not performed here; Phase 4 supplies contradiction candidates and Phase 5 challenges their surrounding literature.
