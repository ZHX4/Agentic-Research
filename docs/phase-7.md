# Phase 7 — Scientific Execution

Phase 7 turns selected Phase 6 hypotheses into reproducible experiment specifications and, when explicitly invoked, executes them inside a restricted Docker sandbox.

## Pipeline

```text
Phase 6 selected hypothesis
        ↓
ExperimentSpec
        ↓
FalsificationPlan
        ↓
Dataset manifests + hashes
        ↓
Docker sandbox policy
        ↓
Multi-seed execution
        ↓
Metrics + stdout/stderr + artifacts
        ↓
Falsification evaluation
        ↓
ExperimentSearchTree
```

## Reproducibility requirements

Every experiment records:

- hypothesis ID;
- command argv;
- planned code path and SHA-256;
- dataset manifests, versions, and SHA-256 hashes;
- seeds;
- primary metric and direction (`higher` or `lower`);
- explicit null hypothesis and rejection criteria;
- sandbox policy;
- container image fingerprint;
- command/environment fingerprints;
- stdout/stderr hashes;
- artifact hashes and sizes;
- per-seed metrics and status.

Code and dataset hashes are rechecked immediately before execution. Dataset directories use deterministic tree hashes over sorted relative paths and file hashes.

## Sandbox safeguards

The default sandbox:

- disables network access;
- drops all Linux capabilities;
- enables `no-new-privileges`;
- uses a read-only root filesystem;
- mounts code read-only;
- mounts datasets read-only;
- mounts only `/outputs` read-write;
- limits memory, CPU, and process count;
- applies a hard execution timeout;
- never interprets experiment argv as Docker arguments;
- does not allow privileged/container-host namespace flags through experiment argv.

GPU access and network access are explicit policy choices; the default is no network and no GPU.

## Metrics contract

Experiments write a JSON array to `$AGENTIC_RESEARCH_OUTPUT_DIR/metrics.json`:

```json
[
  {"name": "accuracy", "value": 0.83, "split": "test"}
]
```

The executor records the seed automatically. Malformed or missing metrics do not become fabricated scientific results.

## Falsification

Phase 7 applies only operationalized prespecified criteria. When `minimum_effect_size` is provided, the configured metric direction is applied (`higher` rejects when the observed value remains below the threshold; `lower` rejects when it remains above it). When no operational threshold is provided, the system reports `inconclusive` rather than pretending that free-form rejection text can be evaluated statistically.

A falsified result requires an explicit rationale. If all seeds do not succeed, falsification remains undecided rather than being inferred from partial failure.

## Experiment search tree

Every planned experiment can start a tree. Results can be appended as replication, mutation, ablation, or branch nodes. Parent and terminal node references are schema-validated.

The CLI accepts an existing tree explicitly with `--base-tree` when extending it.

## CLI

Plan:

```bash
agentic-research-execution plan \
  --hypothesis-run artifacts/hypothesis-run.json \
  --hypothesis-id <HYPOTHESIS_ID> \
  --code experiments/run.py \
  --command python \
  --command run.py \
  --primary-metric accuracy \
  --metric-direction higher \
  --output artifacts/experiment.json
```

Execute:

```bash
agentic-research-execution execute \
  --spec artifacts/experiment.json \
  --code-dir experiments \
  --output-dir artifacts/runs/experiment \
  --result artifacts/results/experiment.json
```

Create a tree:

```bash
agentic-research-execution tree \
  --spec artifacts/experiment.json \
  --output artifacts/results/experiment.tree.json
```

Extend a tree with a result:

```bash
agentic-research-execution tree \
  --spec artifacts/experiment.json \
  --base-tree artifacts/results/experiment.tree.json \
  --result artifacts/results/experiment-result.json \
  --relation replication \
  --output artifacts/results/experiment.tree.updated.json
```

## Scientific boundary

Phase 7 executes and falsifies experiments. It does not:

- generate new hypotheses;
- decide global novelty;
- perform autonomous multi-stage discovery;
- publish papers;
- replace independent review.

Those belong to later phases.
