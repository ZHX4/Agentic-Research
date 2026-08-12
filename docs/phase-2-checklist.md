# Phase 2 Checklist

- [x] Layout-aware PDF blocks with global document order
- [x] Conservative section detection
- [x] Hierarchical section parent assignment
- [x] Same-page section assignment regression protection
- [x] Section-aware chunking
- [x] Table extraction
- [x] Figure/image extraction and caption detection
- [x] Reference extraction
- [x] Numeric citation-edge ingestion
- [x] Common author-year citation-edge ingestion
- [x] Structured candidate field extraction
- [x] Claim extraction
- [x] Explicit Evidence objects
- [x] Claim-to-evidence links
- [x] Raw confidence scores
- [x] Calibration report (ECE, MCE, Brier)
- [x] Isotonic calibration model with serialization
- [x] Content-addressed extraction IDs
- [x] End-to-end paper intelligence pipeline
- [x] `analyze` CLI command
- [x] `calibrate` CLI command
- [x] `fit-calibrator` CLI command
- [x] Offline regression tests
- [x] Phase 2 acceptance documentation
- [ ] Local clean-checkout execution by the developer

The final unchecked item is a local runtime action. It is not treated as a GitHub Actions requirement. The automated test suite intentionally uses deterministic fixtures and mocks rather than depending on live scholarly providers.
