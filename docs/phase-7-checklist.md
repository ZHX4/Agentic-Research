# Phase 7 Acceptance Checklist

- [x] Canonical dataset, falsification, sandbox, experiment, metric, artifact, seed-run, result, and search-tree schemas
- [x] Deterministic experiment planner
- [x] Explicit falsification plan
- [x] Explicit metric direction (`higher` / `lower`)
- [x] Code SHA-256 verification before execution
- [x] Dataset SHA-256/tree-hash verification before mounting
- [x] Multi-seed execution
- [x] Restricted Docker sandbox
- [x] Default network isolation
- [x] Dropped Linux capabilities
- [x] no-new-privileges
- [x] Read-only code and dataset mounts
- [x] Dedicated writable output mount
- [x] CPU/memory/PID limits
- [x] Hard execution timeout
- [x] stdout/stderr hashing
- [x] Artifact hashing and collection
- [x] Structured metrics ingestion
- [x] Explicit falsification evaluation
- [x] Inconclusive result when no operational threshold is specified
- [x] Reproducibility flag based on multi-seed consistency
- [x] Structured rejection for execution preflight/environment failures
- [x] Experiment search tree
- [x] Dedicated Phase 7 CLI
- [x] Offline regression tests
- [x] Documentation and configuration
- [x] Explicit Phase 7 / Phase 8 boundary

Phase 7 does not perform benchmarking at population scale, autonomous discovery, independent review, or publication. Those belong to later phases.
