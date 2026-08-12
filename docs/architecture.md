# Architecture

## Current foundation

The MVP is intentionally deterministic. It defines domain contracts and one candidate-gap detector without requiring an LLM or external API.

```text
JSONL corpus
    |
    v
Paper schema validation
    |
    v
Candidate Gap Detector
    |
    v
GapCandidate objects
```

## Target architecture

```text
ResearchGoal
  -> LiteraturePlanner
  -> SourceAdapters
  -> HybridRetriever
  -> PaperParser
  -> ScientificExtractor
  -> EvidenceStore
  -> ScientificKnowledgeGraph
  -> GapHunter
  -> DevilAdvocate
  -> NoveltyVerifier
  -> HypothesisFactory
  -> HypothesisTournament
  -> ExperimentPlanner
  -> SandboxedExecutor
  -> Falsifier
  -> IndependentReview
  -> Provenance-aware Report
```

## Design rules

- Core schemas must not depend on a model vendor SDK.
- Agents receive structured context and return structured results.
- Retrieval providers are adapters behind stable interfaces.
- Persistence can evolve from JSONL to PostgreSQL/pgvector without changing domain schemas.
- Long-running state belongs in a durable run state store, not in chat history.
- Experiment execution must be isolated from the host.
- Every major decision receives a provenance link.

## Planned storage split

- PostgreSQL: canonical metadata, runs, hypotheses, experiments, provenance.
- pgvector: semantic retrieval where appropriate.
- Graph store (later): scientific relationships and graph traversal.
- Object storage: PDFs, tables, figures, logs, experiment artifacts.
- Redis (later): queues, short-lived locks, rate-limit state.

## Agent boundaries

### Literature planner
Converts a research goal into search facets and retrieval plans.

### Paper intelligence
Extracts structured scientific fields and evidence references.

### Gap hunter
Finds candidate missing combinations, contradictions, underexplored conditions, unresolved limitations, and cross-domain connections.

### Devil's advocate
Attempts to disprove a gap using alternative terminology and broader search.

### Novelty verifier
Compares the surviving candidate against nearest prior work and records the differences and remaining uncertainty.

### Hypothesis factory
Generates diverse hypotheses grounded in surviving gaps.

### Tournament
Ranks hypotheses using novelty, evidence, significance, feasibility, expected information gain, and diversity.

### Experiment planner
Creates a falsifiable experiment plan with datasets, baselines, ablations, metrics, seeds, compute limits, and rejection criteria.

### Falsifier
Actively searches for a cheap decisive experiment that could reject the hypothesis.
