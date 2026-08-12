# Implementation roadmap

## Phase 0 — Foundation (implemented)
- [x] Canonical scientific schemas, deterministic ingestion, contracts, provenance, CLI, tests, documentation

## Phase 1 — Literature intelligence (implemented)
- [x] OpenAlex, Semantic Scholar, arXiv adapters
- [x] canonical identity/deduplication
- [x] rate limiting/retry and temporal cutoff
- [x] full-text acquisition and PDF/HTML parsing

## Phase 2 — Evidence-grounded paper intelligence (implemented)
- [x] layout/section/chunk extraction
- [x] tables/figures/references/citations
- [x] candidate fields, claims, evidence and calibration
- [x] deterministic paper-analysis pipeline

## Phase 3 — Retrieval and world model (implemented)
- [x] lexical/dense/hybrid retrieval and reranking
- [x] temporal/metadata filters
- [x] persistent SQLite scientific world model and citation traversal

## Phase 4 — Gap discovery (implemented)
- [x] missing combinations
- [x] contradictions
- [x] underexplored conditions
- [x] recurring limitations
- [x] cross-domain signals
- [x] graph negative-space signals
- [x] candidate-only status and provenance

## Phase 5 — Adversarial novelty (implemented)
- [x] Devil's Advocate interface
- [x] deterministic query expansion
- [x] local/external prior-work search
- [x] direct/near/contextual matching
- [x] counterevidence and coverage
- [x] temporal integrity
- [x] bounded PDF/HTML deep verification
- [x] deep evidence provenance and required-check safeguard

## Phase 6 — Hypothesis reasoning (implemented)
- [x] hypothesis factory with multiple generation strategies
- [x] evidence/status-aware scoring
- [x] diversity filtering and clustering
- [x] structured reflection and confounder analysis
- [x] deterministic tournament ranking
- [x] bounded evolution/revision
- [x] Pareto frontier across novelty/significance/feasibility
- [x] deterministic run artifacts with lineage/integrity checks
- [x] dedicated hypothesis CLI
- [x] offline regression tests

## Phase 7 — Scientific execution
- experiment planner
- falsification planning
- Docker sandbox
- dataset manifests
- multi-seed execution
- metrics and artifact collection
- experiment search tree

## Phase 8 — Evaluation
- retrieval benchmark
- extraction benchmark
- gap benchmark
- novelty benchmark
- temporal benchmark
- human evaluation
- baseline reproduction
- ablations
- cost/compute accounting

## Phase 9 — Autonomous discovery
- closed-loop research runs
- durable state
- experiment checkpointing
- independent reviewer agents
- provenance-aware reporting

## Phase 10 — Publication
- system paper
- benchmark paper
- validated discovery case study
- reproducibility package
- model/provider disclosure
- licensing audit

> Live GitHub Actions execution can be unavailable when the GitHub account is billing-locked. Phase acceptance does not claim a CI pass unless GitHub actually started the job.
