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

Phase 3
  Phase 2 StructuredExtraction
      -> SQLite scientific world model
      -> FTS5/BM25 lexical retrieval
      -> Embedding provider + dense retrieval
      -> RRF hybrid fusion
      -> Metadata / temporal filtering
      -> Reranking
      -> Directional citation traversal

Phase 4
  ScientificWorldModel
      -> Missing-combination signals
      -> Contradiction signals
      -> Underexplored-condition signals
      -> Recurring-limitation signals
      -> Cross-domain signals
      -> Graph negative-space signals
      -> Candidate Gap objects with provenance

Phase 5
  Phase 4 candidates
      -> Devil's Advocate
      -> Deterministic query expansion
      -> Local + external literature search
      -> Prior-work comparison
      -> Counterevidence registry
      -> Coverage assessment
      -> Conservative novelty verdict
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
- Phase 4 gap detection is corpus-relative structural discovery, never novelty verification.
- Phase 4 candidates retain supporting paper IDs and canonical world-model entity node IDs.
- Phase 4 never changes a candidate away from `status="candidate"`.
- Phase 5 accepts only Phase 4 candidates.
- Phase 5 treats failed/empty search as uncertainty, never proof of novelty.
- `supported` in Phase 5 means “survived the configured search budget”, not globally proven novel.
- Temporal cutoff verification excludes future and unknown-year papers.
- Experiment execution must be isolated from the host.
- Every major decision receives a provenance link.
- Hybrid retrieval never combines incomparable lexical and dense raw scores; it fuses ranked lists with Reciprocal Rank Fusion.
- Dense vectors are isolated by exact embedding-model identity.

## Phase 3 storage

Phase 3 uses a local SQLite world model as the canonical research-development implementation. It contains:

- paper metadata;
- structured nodes for sections, chunks, claims, evidence, references, authors, methods, datasets, metrics, baselines, and tasks;
- typed relationship edges;
- FTS5 lexical index;
- float32 embeddings with model identity;
- enough information to reproduce retrieval results from the stored corpus.

## Phase 4 gap discovery inputs

Phase 4 reads the Phase 3 world model directly and does not mutate its scientific facts. The discovery engine creates a deterministic result containing:

- corpus snapshot size;
- detector signals with support/provenance;
- candidate `GapCandidate` objects;
- temporal cutoff used;
- deterministic run fingerprint.

The engine uses deterministic normalization and thresholds so offline runs are reproducible.

## Phase 5 adversarial verification

Phase 5 is deliberately separated from Phase 4. It can challenge candidates using:

- the local indexed world model;
- configured OpenAlex/Semantic Scholar/arXiv-backed literature service;
- deterministic terminology expansions;
- exact/near/contextual prior-work comparison;
- counterevidence records;
- search-coverage and uncertainty reporting.

The result is an auditable `NoveltyVerificationReport`. A lack of matches cannot become a global novelty proof because the report always retains its search budget, coverage, sources, and limitations.

## Planned production storage

- PostgreSQL: canonical metadata, runs, hypotheses, experiments, provenance.
- pgvector: high-scale semantic retrieval where appropriate.
- Graph store: high-scale scientific relationships and traversal when SQLite is no longer sufficient.
- Object storage: PDFs, tables, figures, logs, experiment artifacts.
- Redis: queues, short-lived locks, and distributed rate-limit state when needed.

## Current Phase 4 limitations

- Contradiction detection uses deterministic result-polarity markers and cannot resolve complex conditional scientific claims.
- Condition detection currently depends on structured metadata fields and does not infer every condition from prose.
- Recurring limitation signals are candidates; they do not prove that a limitation is unresolved globally.
- Cross-domain detection requires explicit domain metadata.
- Graph negative-space analysis identifies structural holes, not technical feasibility.

## Current Phase 5 limitations

- Query expansion uses a small deterministic alias set rather than a complete ontology or LLM-generated synonym search.
- Prior-work similarity is interpretable lexical/field overlap, not proof of semantic equivalence.
- External search coverage depends on configured providers, rate limits, indexing, and query budgets.
- The system cannot establish that no unpublished, inaccessible, or differently worded work exists.
- Phase 5 does not generate hypotheses or experiments; those belong to later phases.
