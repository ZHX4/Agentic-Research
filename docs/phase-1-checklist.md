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
- [x] Offline adapter/transport/identity/full-text/service tests
- [x] Phase 1 acceptance documentation
- [ ] Live provider smoke test by the developer

The final unchecked item is intentionally a live-network verification step. The Phase 1 automated suite uses deterministic mocks and does not require provider credentials or network access.
