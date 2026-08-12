# Phase 1 Checklist

- [x] OpenAlex adapter
- [x] Semantic Scholar adapter
- [x] arXiv adapter
- [x] Shared HTTP transport
- [x] Retry policy and `Retry-After` handling
- [x] Conservative provider-specific rate limiting
- [x] Provider environment settings
- [x] Canonical DOI normalization
- [x] Canonical arXiv normalization
- [x] Cross-source canonical identity and deterministic deduplication
- [x] Temporal cutoff enforcement
- [x] Cross-provider literature service
- [x] Open full-text URL discovery
- [x] Full-text acquisition manifests
- [x] SHA-256 artifact hashing
- [x] PDF parsing
- [x] HTML parsing
- [x] Phase 1 CLI commands (`search`, `acquire`, `parse`)
- [x] Offline adapter/transport/identity/full-text/service/CLI tests
- [x] Phase 1 acceptance documentation

## Optional operator verification

A developer with provider credentials may run a live search against each service after checkout. This is an operational smoke test, not a prerequisite for the deterministic Phase 1 implementation or its automated test suite.
