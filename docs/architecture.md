# Architecture

## Implemented layers

The repository is intentionally built as deterministic, provider-agnostic layers. Each phase adds capability without collapsing the scientific provenance model.

```text
Phase 0
  JSONL corpus
      -> Paper schema validation
      -> Candidate Gap Detector
      -> Provenance contracts

Phase 1
  Scholarly source adapters
      -> OpenAlex / Semantic Scholar / arXiv
      -> Retry + rate limiting
      -> Canonical identity + deduplication
      -> Temporal cutoff
      -> Full-text acquisition
      -> PDF / HTML parsing

Phase 2
  Acquired PDF
      -> Layout-aware blocks
      -> Section hierarchy
      -> Section-aware chunks
      -> Tables / figures
      -> References / citation edges
      -> Structured candidate fields
      -> Claims + Evidence
      -> Confidence calibration
```

## Target architecture

```text
ResearchGoal
  -> LiteraturePlanner
  -> SourceAdapters
  -> LiteratureService
  -> PaperIntelligence
  -> HybridRetriever (Phase 3)
  -> ScientificWorldModel (Phase 3)
  -> GapHunter (Phase 4)
  -> DevilAdvocate (Phase 5)
  -> NoveltyVerifier (Phase 5)
  -> HypothesisFactory (Phase 6)
  -> HypothesisTournament (Phase 6)
  -> ExperimentPlanner (Phase 7)
  -> SandboxedExecutor (Phase 7)
  -> Falsifier (Phase 7)
  -> Evaluation + TemporalBenchmark (Phase 8)
  -> AutonomousDiscovery (Phase 9)
  -> Provenance-aware Report / Papers (Phase 10)
```

## Design rules

- Core schemas must not depend on a model vendor SDK.
- Agents receive structured context and return structured results.
- Retrieval providers are adapters behind stable interfaces.
- Phase 2 extraction is deterministic and auditable; LLM extraction is intentionally deferred.
- Extracted fields are candidate data, not truth.
- Every extracted claim has an explicit Evidence object and source chunk.
- Confidence is raw until calibrated against labeled examples.
- Missing retrieval results never constitute proof of novelty.
- Long-running state belongs in a durable run state store, not in chat history.
- Experiment execution must be isolated from the host.
- Every major decision receives a provenance link.

## Planned storage split

- PostgreSQL: canonical metadata, runs, hypotheses, experiments, provenance.
- pgvector: semantic retrieval where appropriate (Phase 3).
- Graph store: scientific relationships and traversal (Phase 3+).
- Object storage: PDFs, tables, figures, logs, experiment artifacts.
- Redis: queues, short-lived locks, and distributed rate-limit state when needed.

## Current Phase 2 limitations

- No OCR for scanned/image-only PDFs.
- Citation resolution is deterministic and conservative; unusual citation styles may remain unresolved.
- Table/figure extraction can miss complex layouts.
- Candidate entity extraction is heuristic and must not be treated as scientific truth.
- Confidence calibration requires labeled examples collected outside the extractor.
