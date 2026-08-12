# Phase 4 — Scientific Gap Discovery

Phase 4 analyzes the Phase 3 scientific world model and produces **candidate research gaps only**. It never claims global novelty, performs adversarial review, or changes a candidate into a verified status. Those responsibilities begin in Phase 5.

## Implemented detectors

1. **Missing combinations** — method/dataset/task or method/task combinations that are independently represented in the corpus but have no direct indexed co-occurrence in the relevant context.
2. **Contradictions** — opposing positive/negative result claims sharing a normalized topic across distinct papers.
3. **Underexplored conditions** — metadata-backed conditions with unusually low coverage inside an observed method/task pair.
4. **Recurring limitations** — repeated limitation themes across papers, represented as candidate unresolved limitations.
5. **Cross-domain connections** — entities represented in distinct domains whose direct combination is absent from the indexed corpus.
6. **Graph negative space** — method/dataset pairs with shared task neighbors but no direct co-occurrence (common-neighbor structural holes).

## Scientific safeguards

- Every candidate is emitted with `status="candidate"`.
- Candidate claims are explicitly corpus-relative; absence from the corpus is not proof of novelty.
- Each signal carries paper IDs and actual world-model node IDs for provenance.
- Deterministic IDs are content-derived, and the discovery `run_id` includes a fingerprint of the indexed snapshot plus configuration.
- Temporal cutoffs exclude future papers and papers with unknown years when a cutoff is requested.
- Detector thresholds are configurable and stored in the discovery result's reproducible configuration context.
- Phase 5 must perform query expansion, broader literature search, counterevidence search, nearest-prior-work comparison, and novelty uncertainty reporting.

## CLI

```bash
python -m agentic_research.cli discover-gaps \
  --database artifacts/world-model.sqlite \
  --output artifacts/gap-discovery.json
```

Restrict the detector set when debugging or benchmarking:

```bash
python -m agentic_research.cli discover-gaps \
  --database artifacts/world-model.sqlite \
  --output artifacts/gaps.json \
  --include-type contradiction \
  --include-type graph_negative_space
```

Historical evaluation:

```bash
python -m agentic_research.cli discover-gaps \
  --database artifacts/world-model.sqlite \
  --output artifacts/gaps-2022.json \
  --temporal-cutoff 2022
```

## Data contract

`GapDiscoveryResult` contains:

- `run_id`
- `temporal_cutoff`
- `corpus_paper_count`
- `signals`
- `candidates`

A `GapSignal` contains the detector type, statement, supporting papers, actual graph node IDs, normalized entity values where applicable, support count, structural score, and provenance descriptors.

## Deliberate limitations

- Deterministic polarity detection is conservative and cannot resolve context-dependent scientific contradictions.
- Condition detection currently relies on structured metadata fields from the indexed corpus; it does not infer missing experimental conditions from raw prose.
- Recurring limitations are candidates, not proof that nobody has addressed the limitation.
- Cross-domain analysis requires explicit domain metadata.
- Structural holes are graph signals, not evidence of technical feasibility.
- The engine does not perform external literature search, novelty verification, or LLM reasoning.
