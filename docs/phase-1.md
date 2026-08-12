# Phase 1 — Literature Intelligence Acceptance Gate

Phase 1 turns the deterministic Phase 0 corpus interface into a real literature-access layer. It is responsible for source access, normalization, deduplication, temporal filtering, retry/rate-limit handling, open full-text acquisition, and basic PDF/HTML parsing.

## Implemented scope

- OpenAlex Works search adapter
- Semantic Scholar Academic Graph paper search adapter
- arXiv Atom search adapter
- provider-independent HTTP transport
- conservative per-provider rate limiting
- retry handling for transient HTTP failures and `429 Retry-After`
- environment-backed provider configuration
- canonical DOI normalization
- canonical arXiv identifier normalization (revision suffix removed for work identity)
- source identifiers retained in paper metadata
- deterministic cross-source deduplication
- cross-provider literature service
- temporal cutoff enforcement in all three adapters
- full-text candidate URL discovery
- PDF/HTML acquisition manifests with SHA-256 and byte counts
- PDF text extraction
- HTML text extraction with executable/content-noise tags removed
- CLI commands for search, acquisition, and parsing
- offline tests using HTTP mocks; tests never depend on live provider availability

## Explicit non-goals

Phase 1 does not implement:

- embeddings
- vector databases
- semantic reranking
- citation traversal or graph persistence
- LLM-based paper extraction
- evidence calibration
- gap verification
- novelty verification
- hypothesis generation
- experiment execution

Those belong to later phases in `docs/roadmap.md`.

## Source assumptions

OpenAlex Works documentation: https://developers.openalex.org/api-reference/works/list-works

OpenAlex pagination documentation: https://developers.openalex.org/guides/page-through-results

Semantic Scholar API overview: https://webflow.semanticscholar.org/product/api

Semantic Scholar API tutorial and pagination/rate-limit guidance: https://webflow.semanticscholar.org/product/api/tutorial

The arXiv adapter uses the public Atom query endpoint and a conservative three-second minimum interval configured by default. The interval is a client-side safety default and is not treated as an official service limit.

## Acceptance criteria

A clean checkout is considered Phase 1 complete when:

1. `pip install -e .[dev]` installs the new Phase 1 dependencies.
2. `python -m agentic_research.cli --help` exposes `search`, `acquire`, and `parse`.
3. `python -m agentic_research.cli demo` still works without network access.
4. All source adapters can be exercised with deterministic mocked HTTP responses.
5. Cross-source duplicate papers collapse to one canonical record when DOI, arXiv ID, source ID, or deterministic title/author/year fingerprints establish identity.
6. A temporal cutoff can never return a paper newer than the cutoff.
7. Retryable HTTP failures are retried; `Retry-After` is honored for `429` responses when supplied.
8. Full-text manifests contain source, URLs, status, media type, byte count, SHA-256, and retrieval timestamp.
9. PDF and HTML documents can be parsed into deterministic plain-text documents.
10. No Phase 1 component makes a novelty claim merely because a provider returned no result.
11. Network-dependent tests are absent; provider tests use mocks.
12. No API key or credential is committed.

## Reproducibility

Provider output itself is external and time-varying. Phase 1 therefore records source identifiers and retrieval metadata, while deterministic tests use frozen mock responses. Later phases will add immutable corpus snapshots/manifests and temporal benchmark controls.
