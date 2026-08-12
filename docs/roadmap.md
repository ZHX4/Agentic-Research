# Implementation roadmap

## Phase 0 — Foundation (implemented)

- Canonical paper/evidence/gap/hypothesis/experiment schemas
- Deterministic local JSONL ingestion
- Candidate missing-combination detector
- Provider-agnostic agent and retrieval contracts
- Provenance contract
- CLI
- CI
- Research methodology and architecture docs

## Phase 1 — Literature intelligence (implemented)

- [x] OpenAlex adapter
- [x] Semantic Scholar adapter
- [x] arXiv adapter
- [x] canonical identity + deduplication
- [x] rate limiting and retry policy
- [x] temporal cutoff enforcement
- [x] full-text acquisition manifests
- [x] PDF/HTML parsing

## Phase 2 — Evidence-grounded paper intelligence (implemented)

- [x] layout-aware text blocks and section hierarchy
- [x] section-aware chunking
- [x] table extraction
- [x] figure/image extraction and caption detection
- [x] structured candidate field extraction
- [x] claim/evidence linking
- [x] extraction confidence calibration
- [x] citation graph ingestion
- [x] deterministic end-to-end paper analysis

## Phase 3 — Retrieval and world model (implemented)

- [x] lexical retrieval
- [x] embedding retrieval
- [x] reranking
- [x] citation traversal
- [x] metadata filters
- [x] temporal filtering
- [x] hybrid retrieval with Reciprocal Rank Fusion
- [x] scientific knowledge graph/world model
- [x] model-isolated vector storage
- [x] persistent SQLite world model
- [x] retrieval CLI
- [x] deterministic offline regression coverage

## Phase 4 — Gap discovery (implemented)

- [x] missing combinations
- [x] contradictions
- [x] underexplored conditions
- [x] unresolved limitation candidates
- [x] cross-domain connections
- [x] graph-based negative-space analysis
- [x] actual world-model node provenance
- [x] temporal cutoff
- [x] deterministic discovery fingerprint
- [x] configurable thresholds
- [x] `discover-gaps` CLI
- [x] regression coverage
- [x] candidate-only status enforcement

## Phase 5 — Adversarial novelty (implemented)

- [x] Devil's Advocate agent interface
- [x] deterministic query expansion
- [x] fixed alternate-terminology probes
- [x] local world-model search
- [x] configured external scholarly search
- [x] nearest-prior-work comparison
- [x] direct / near / contextual classification
- [x] counterevidence registry
- [x] conservative novelty verdicts
- [x] search-coverage reporting
- [x] temporal cutoff with unknown-year exclusion
- [x] bounded full-text verification
- [x] PDF verification through Phase 2 intelligence
- [x] HTML same-context verification
- [x] deep-evidence provenance and artifact hashes
- [x] required-deep-check safeguard
- [x] status-transition control
- [x] batch verification report
- [x] dedicated verification CLI
- [x] offline regression coverage

> Live GitHub Actions execution may be unavailable when the GitHub account is billing-locked. The Phase 5 acceptance gate therefore does not claim a live CI pass when GitHub did not start the job.

## Phase 6 — Hypothesis reasoning

- hypothesis factory
- diversity control
- clustering and deduplication
- tournament ranking
- evolution/reflection
- Pareto ranking across novelty/significance/feasibility

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
