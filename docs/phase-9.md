# Phase 9 — Autonomous Discovery

Phase 9 is the durable control plane above Phases 4–8. It orchestrates the canonical stage implementations through explicit, injectable Python adapters and never duplicates their scientific logic.

```text
Gap → Verify → Hypothesis → Execute → Evaluate → Review → Report → next iteration
```

The controller persists `AutonomousRunState` in SQLite, writes checkpoint snapshots, verifies SHA-256 integrity on resume, bounds retries and iterations, detects no-progress loops, and stops on critical reviewer rejection.

## Production adapter contract

A production run must provide an adapter manifest whose six stage entries are `module:function` references:

```json
{
  "stages": {
    "gap": "your_adapters:run_gap",
    "verify": "your_adapters:run_verify",
    "hypothesis": "your_adapters:run_hypothesis",
    "execute": "your_adapters:run_execute",
    "evaluate": "your_adapters:run_evaluate",
    "report": "your_adapters:run_report"
  }
}
```

Each callable receives one JSON-compatible dictionary and must return one JSON-compatible dictionary. The controller records each stage's input/output hashes, persists its output artifact, harvests provenance IDs, and will not silently rerun a completed stage whose artifact hash still matches the checkpoint.

Run the real control plane with:

```bash
agentic-research-autonomous run \
  --run-id run-001 \
  --input-file artifacts/phase9-input.json \
  --adapters-file configs/phase9.adapters.json \
  --output artifacts/phase9-report.json
```

Resume from durable state with:

```bash
agentic-research-autonomous resume \
  --run-id run-001 \
  --adapters-file configs/phase9.adapters.json \
  --output artifacts/phase9-report.json
```

`--offline-smoke-test` is available only for deterministic control-plane tests; it is not the production path and must not be used to claim scientific discovery.

## Independent review

The default panel contains separate provenance and scientific-integrity reviewers. Additional reviewer implementations can be injected through the `Reviewer` interface. A critical reviewer rejection stops the run by policy.

## Boundaries

Phase 9 may select, execute, evaluate, review, retry, checkpoint, and resume research work. It does not publish papers or automate publication. Those responsibilities remain in Phase 10.
