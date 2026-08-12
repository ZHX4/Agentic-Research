# Phase 3 — Retrieval and Scientific World Model

Phase 3 turns the structured paper intelligence produced by Phase 2 into a persistent, queryable scientific representation. It implements lexical retrieval, dense retrieval, hybrid rank fusion, reranking, metadata filtering, citation traversal, and a durable scientific world model.

## Implemented scope

- SQLite-backed scientific world model with FTS5 lexical index
- persistent paper, section, chunk, claim, evidence, reference, entity, and citation nodes
- typed edges for provenance, citation, authorship, methods, datasets, metrics, baselines, and tasks
- deterministic SHA-1 identities for normalized entity nodes
- explicit external-paper nodes for DOI/arXiv citation targets
- directional graph traversal (`out`, `in`, `both`)
- lexical retrieval using SQLite FTS5/BM25 ranking
- pluggable embedding provider contract
- deterministic hash embedding baseline for offline tests
- production SentenceTransformers embedding adapter
- vector persistence with float32 storage
- embedding-model identity isolation
- temporal and metadata filters shared by lexical and dense retrieval
- dense cosine retrieval by vector scan
- Reciprocal Rank Fusion for combining lexical and dense rankings
- deterministic lexical-overlap reranker
- optional SentenceTransformers CrossEncoder reranker
- retrieval provenance in every returned hit
- CLI commands: `index`, `retrieve`, and `traverse`
- offline regression tests for indexing, hybrid retrieval, temporal cutoffs, vector-model isolation, reranking, and graph traversal

## Scientific integrity rules

1. Lexical and dense scores are never directly mixed; hybrid retrieval uses Reciprocal Rank Fusion over rankings.
2. Dense retrieval is isolated by exact embedding model identity. Vectors from different embedding models are never compared.
3. Temporal cutoffs are applied before dense ranking and before lexical ranking is returned.
4. Citation edges never invent a cited paper record. DOI/arXiv-resolved citations create explicit external-paper nodes; unresolved citations retain their reference node.
5. The world model preserves Phase 2 provenance objects rather than replacing them with summaries.
6. Hash embeddings are an offline deterministic baseline only; they are not represented as semantic quality comparable to a trained embedding model.
7. Retrieval output is evidence retrieval, not novelty verification or scientific truth.
8. No gap discovery, contradiction reasoning, novelty judgment, hypothesis generation, or experiment execution is performed in Phase 3.

## Production embedding and reranking

The core package remains lightweight. Install the optional `embeddings` extra to use SentenceTransformers for embeddings and CrossEncoder reranking. SentenceTransformers currently supports both embedding and CrossEncoder reranking workflows. See the official package documentation before selecting a model.

## Example

Create a Phase 2 analysis:

```bash
python -m agentic_research.cli analyze \
  --paper artifacts/paper.json \
  --pdf artifacts/paper.pdf \
  --output artifacts/paper-intelligence.json
```

Index it:

```bash
python -m agentic_research.cli index \
  --input artifacts/paper-intelligence.json \
  --database artifacts/world-model.sqlite \
  --embedding sentence-transformers
```

Search it:

```bash
python -m agentic_research.cli retrieve \
  "retrieval factual accuracy" \
  --database artifacts/world-model.sqlite \
  --mode hybrid \
  --embedding sentence-transformers \
  --reranker cross-encoder
```

Traverse citations:

```bash
python -m agentic_research.cli traverse \
  "paper:paper-id" \
  --database artifacts/world-model.sqlite \
  --depth 2 \
  --edge-type cites \
  --direction out
```

## Acceptance gate

Phase 3 is complete when:

1. Phase 0–2 contracts remain compatible;
2. a Phase 2 extraction indexes into a persistent SQLite world model;
3. FTS5 lexical retrieval returns deterministic hits;
4. embedding indexing and dense retrieval use a verified model identity;
5. hybrid retrieval uses rank fusion rather than incomparable raw scores;
6. metadata and temporal filters apply to both retrieval modes;
7. reranking is pluggable and provenance is retained;
8. citations can be traversed directionally;
9. entity IDs are deterministic across processes;
10. the CLI exposes `index`, `retrieve`, and `traverse`;
11. offline tests cover the complete Phase 3 path;
12. no Phase 4+ reasoning is claimed by Phase 3.
