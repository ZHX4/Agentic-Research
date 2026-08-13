# Phase 9 — Autonomous Discovery

Phase 9 is the durable control plane above Phases 4–8. It orchestrates the canonical stage implementations through explicit adapters instead of duplicating their scientific logic.

```text
Gap → Verify → Hypothesis → Execute → Evaluate → Review → Report → next iteration
```

The controller persists `AutonomousRunState` in SQLite, writes immutable checkpoint snapshots, verifies SHA-256 integrity on resume, bounds retries and iterations, detects no-progress loops, and stops on critical reviewer rejection.

Each stage adapter returns a JSON object. Stage outputs are persisted as artifacts with input/output hashes. Provenance IDs harvested from outputs are stored on the durable run state and included in the final deterministic report.

Phase 9 requires a reviewer panel. The repository provides deterministic structural/provenance reviewers for offline testing and supports injected independent reviewer implementations via the `Reviewer` interface.

The bundled CLI is a safe control-plane smoke path using identity adapters. Production deployments inject adapters connected to the existing Phase 4–8 services.

```bash
agentic-research-autonomous run --run-id run-001 --input-file artifacts/input.json --output artifacts/phase9-report.json
agentic-research-autonomous resume --run-id run-001 --output artifacts/phase9-report.json
```

Phase 9 does not publish papers or automate publication. Those responsibilities remain in Phase 10.
