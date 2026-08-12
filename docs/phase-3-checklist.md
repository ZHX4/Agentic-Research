# Phase 3 Acceptance Checklist

- [x] Persistent SQLite scientific world model
- [x] FTS5/BM25 lexical retrieval
- [x] Unicode-safe lexical query tokenization
- [x] Pluggable embedding interface
- [x] Deterministic offline embedding baseline
- [x] Production SentenceTransformers embedding adapter
- [x] Embedding-model isolation
- [x] Dense cosine retrieval
- [x] Reciprocal Rank Fusion hybrid retrieval
- [x] Metadata filters
- [x] Temporal cutoff enforcement
- [x] Deterministic lexical reranker
- [x] CrossEncoder reranker adapter with raw score preservation
- [x] Directional citation traversal
- [x] Citation/external-paper nodes
- [x] Stable entity node IDs
- [x] Phase 2 provenance preservation
- [x] Vector corruption detection
- [x] Idempotent re-indexing with vector preservation
- [x] `index` CLI command
- [x] `retrieve` CLI command
- [x] `traverse` CLI command
- [x] Regression tests for indexing, retrieval, filtering, Unicode queries, model isolation, reranking, graph traversal, and vector corruption
- [x] Phase 3 architecture documentation
- [x] Phase 3 acceptance definition

## Runtime verification note

GitHub Actions is configured to run installation, Ruff lint/format checks, strict mypy, and pytest. The latest Actions jobs were not started because GitHub reports that the account is locked due to a billing issue. This is an external account/infrastructure failure, not a repository test result.

The implementation has therefore been hardening-reviewed and covered by deterministic offline regression tests, but live CI execution of the current checkout remains blocked until the account billing lock is resolved.
