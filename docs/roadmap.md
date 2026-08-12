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

## Phase 3 — Retrieval and world model

- lexical retrieval
- embedding retrieval
- reranking
- citation traversal
- metadata filters
- hybrid retrieval
- scientific knowledge graph

## Phase 4 — Gap discovery

- missing combinations
- contradictions
- underexplored conditions
- unresolved limitations
- cross-domain connections
- graph-based negative-space analysis

## Phase 5 — Adversarial novelty

- Devil's Advocate agent
- query expansion
- alternate terminology search
- nearest-prior-work comparison
- counterevidence registry
- novelty uncertainty reporting

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
