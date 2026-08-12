# Architecture

## Implemented layers

```text
Phase 0
  corpus -> schemas -> provenance -> deterministic candidate gaps

Phase 1
  scholarly providers -> canonical identity -> dedup -> full text

Phase 2
  PDF/HTML -> layout -> sections/chunks -> tables/figures -> claims/evidence/citations

Phase 3
  extraction -> SQLite world model -> lexical/dense/hybrid retrieval -> reranking -> graph traversal

Phase 4
  world model -> missing combinations / contradictions / underexplored conditions / limitations / cross-domain / graph negative-space

Phase 5
  gap candidate -> adversarial query expansion -> local/external prior work -> bounded deep full-text verification -> counterevidence -> conservative verdict

Phase 6
  verified gap -> hypothesis factory -> diversity filtering/clustering -> reflection -> tournament -> bounded evolution -> Pareto frontier
```

## Phase 6 design rules

- Phase 6 accepts only status-eligible Phase 5 gaps.
- Hypotheses retain their upstream gap IDs and statuses.
- Every hypothesis has an explicit falsification condition.
- Reflection is structured and separate from generation.
- Near-duplicate removal is deterministic.
- Clustering is deterministic and is not treated as a semantic truth judgment.
- Tournament selection has deterministic tie-breaking.
- Evolution is bounded by an explicit generation limit.
- Pareto selection optimizes novelty/significance/feasibility; it does not establish correctness.
- Evolved candidates and lineage are serialized in the final run artifact.
- No code is executed and no experiment is considered validated in Phase 6.

## Target architecture

```text
ResearchGoal
  -> LiteraturePlanner
  -> SourceAdapters
  -> LiteratureService
  -> PaperIntelligence
  -> HybridRetriever
  -> ScientificWorldModel
  -> GapHunter
  -> DevilAdvocate
  -> NoveltyVerifier
  -> HypothesisFactory
  -> HypothesisTournament
  -> ExperimentPlanner (Phase 7)
  -> SandboxedExecutor (Phase 7)
  -> Falsifier (Phase 7)
  -> Evaluation + TemporalBenchmark (Phase 8)
  -> AutonomousDiscovery (Phase 9)
  -> Provenance-aware Reports/Papers (Phase 10)
```
