# Phase 2 — Evidence-Grounded Paper Intelligence

Phase 2 converts acquired full-text documents from Phase 1 into auditable scientific structure. It deliberately remains deterministic and explainable: no embeddings, vector search, LLM reasoning, novelty verification, or experiment execution is introduced here.

## Implemented scope

- layout-aware PDF block extraction with global document order
- conservative section detection and hierarchical parent assignment
- same-page section assignment based on block order
- section-aware text chunking with size limits
- native PDF table extraction through PyMuPDF `Page.find_tables()`
- embedded image/figure extraction with SHA-like image identifiers and nearby figure-caption detection
- bibliography/reference segmentation
- DOI/arXiv normalization for references
- numeric citation marker extraction and citation-edge ingestion
- structured candidate fields for methods, datasets, metrics, baselines, limitations, assumptions, and future work
- deterministic claim extraction with explicit claim types and raw confidence
- explicit `Evidence` records linked to claims via `ClaimEvidenceLink`
- calibration metrics: ECE, MCE, and Brier score
- isotonic confidence calibration with a serializable calibration model
- one-command end-to-end PDF analysis
- offline regression tests for sections, chunking, citations, tables, figures, claims, evidence, calibration, pipeline, and CLI

## Scientific integrity rules

1. Extracted fields are explicitly marked as **candidates** in Paper metadata. They are not treated as ground truth.
2. Extracted claims are evidence candidates; the extraction layer does not assert that the claims are scientifically true.
3. Every claim produced by the pipeline has a source chunk and an explicit `Evidence` record.
4. Confidence values are heuristic **raw** confidence until calibrated on labeled examples. No labels are invented by the system.
5. Citation parsing only creates edges when a citation marker resolves to an extracted reference entry.
6. A citation edge with no DOI/arXiv identifier is still preserved as a reference edge, but `cited_paper_id` remains null rather than being guessed.
7. Native table/figure extraction is allowed to miss difficult layouts. The confidence field records extraction confidence instead of fabricating completeness.

## Why PyMuPDF is used

Current PyMuPDF exposes structured `dict`/block extraction and `Page.find_tables()` with cell extraction and markdown conversion. The Phase 2 implementation uses these capabilities while preserving the document coordinates and page numbers needed for evidence provenance.

## Explicit non-goals

The following remain later phases:

- lexical/semantic/vector retrieval
- reranking
- citation traversal/search across external graphs
- scientific knowledge graph persistence
- contradiction analysis
- gap verification
- novelty verification
- LLM-based hypothesis generation
- experiment planning and execution

## Acceptance gate

A clean checkout is considered Phase 2 complete when:

1. the Phase 0 and Phase 1 test suites remain compatible;
2. `Page.find_tables()`-based extraction is covered by an offline PDF fixture;
3. same-page section ordering is covered by a regression test;
4. numeric references generate reproducible citation edges;
5. claims produce explicit evidence IDs and claim/evidence links;
6. calibration produces bounded and monotone mappings from labeled data;
7. the end-to-end pipeline produces a `StructuredExtraction` from a deterministic PDF fixture;
8. CLI `analyze` and `calibrate` are covered by tests;
9. no Phase 2 output is represented as a novelty claim or scientific conclusion.

See `docs/phase-2-checklist.md` for the implementation checklist.
