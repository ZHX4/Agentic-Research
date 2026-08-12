# Phase 5 — Adversarial Novelty Verification

Phase 5 attempts to **disprove** Phase 4 candidate gaps. It performs deterministic query expansion, local-world search, configured external literature search, prior-work comparison, bounded full-text verification, counterevidence registration, and uncertainty reporting.

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
Bounded full-text verification of closest prior work
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

- `disproved`: a direct prior work is established by structured metadata, the local world-model graph, or successful deep full-text verification.
- `weakened`: close prior work materially challenges the candidate but no direct combination was established.
- `supported`: the candidate survived the configured adversarial search budget **and the required deep checks** without a direct or near prior-work match.
- `inconclusive`: search/deep-evidence coverage was insufficient to support or reject the candidate.

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

## Deep full-text verification

The closest configurable number of prior works can be checked against acquired full text. For PDF prior work, the existing Phase 2 paper-intelligence pipeline is reused; for HTML prior work, the parsed text is checked for the candidate entities in the same local context.

Every check records:

- acquisition status;
- media type;
- method/dataset/task presence;
- same-context result;
- local path and content hash when available;
- failure/unavailability reason.

When deep verification is required but no usable full text is available, the verifier **does not** turn search completion into a novelty conclusion; the result remains `inconclusive` unless direct prior work was already established elsewhere.

## Counterevidence

Direct and near matches are registered as explicit counterevidence objects with severity. No paper is automatically treated as counterevidence merely because it is superficially related.

## Temporal integrity

When `temporal_cutoff` is set:

- future papers are excluded;
- papers with unknown publication years are excluded;
- local and external searches use the same cutoff contract;
- deep verification inherits the same cutoff because only eligible search records are considered.

This prevents future-information leakage in historical evaluation.

## Coverage

- `broad`: at least the configured number of successful probes and at least two search sources.
- `moderate`: sufficient successful probes or multiple search sources, but not both broad criteria.
- `limited`: at least one successful search probe.
- `none`: no successful search probe.

Coverage is a search-budget property, not a claim about the completeness of science.

## CLI

```bash
agentic-research-verify verify-gaps \
  --input artifacts/gap-discovery.json \
  --output artifacts/novelty-report.json \
  --database artifacts/world-model.sqlite
```

Bounded deep verification can be tuned with:

```bash
agentic-research-verify verify-gaps \
  --input artifacts/gap-discovery.json \
  --output artifacts/novelty-report.json \
  --database artifacts/world-model.sqlite \
  --max-deep-verifications 5 \
  --deep-verification-similarity-floor 0.45 \
  --fulltext-cache-dir artifacts/phase5-fulltext
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
5. Supported novelty requires the configured deep-verification policy to be satisfied.
6. Direct combinations established by the local graph or deep full text can disprove a candidate regardless of title similarity.
7. `allow_status_transition=False` preserves candidate status while retaining the adversarial verdict.
8. All probes, prior-work matches, deep evidence, counterevidence, coverage, and limitations are serialized.
9. The verifier is deterministic given the same candidate, configuration, provider outputs, and full-text artifacts.
10. Phase 5 does not generate research hypotheses or experiments; those begin in Phase 6+.

## Deliberate limitations

- Query expansion is deterministic and intentionally conservative; it is not a complete synonym generator.
- Similarity is interpretable lexical/field overlap rather than a proof of semantic equivalence.
- External-source coverage depends on the configured provider set, API availability, and search limits.
- Full-text acquisition can fail because papers are paywalled, blocked, malformed, or unavailable.
- The verifier cannot establish that no unpublished or inaccessible work exists.
- HTML deep verification is text-context based; PDF deep verification reuses the stronger Phase 2 structured pipeline.
- A `supported` result is never a global novelty proof.
