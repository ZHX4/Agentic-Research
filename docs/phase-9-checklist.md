# Phase 9 Acceptance Checklist

- [x] Durable SQLite autonomous run state
- [x] Immutable checkpoint snapshots
- [x] State and checkpoint SHA-256 integrity validation
- [x] Resume support
- [x] Bounded iteration budget
- [x] Bounded stage retries
- [x] Configurable no-progress patience
- [x] Canonical Phase 4–8 stage adapter interface
- [x] Independent reviewer interface
- [x] Deterministic structural/provenance reviewers
- [x] Critical-review stop policy
- [x] Provenance harvesting across stages
- [x] Deterministic autonomous run reporting
- [x] Dedicated autonomous CLI
- [x] Offline regression coverage
- [x] Explicit Phase 9 / Phase 10 boundary

The bundled CLI identity adapters are a control-plane smoke path. Production runs inject adapters connected to the canonical Phase 4–8 services.
