# Annotations (templates — no real labels yet)

Status: **NOT YET FROZEN**. No human labels exist. The files here are
machine-readable templates that enforce the protocol shape.

## Label vocabularies

Gap (`kind: gap`): `valid_opportunity`, `already_addressed`,
`partially_addressed`, `ambiguous`, `unsupported`.

Novelty (`kind: novelty`): `direct_prior`, `near_equivalent`,
`related_not_disqualifying`, `no_disqualifying_found`,
`insufficient_evidence`.

## Workflow

1. Annotator A and annotator B label independently
   (`gap_labels.A.template.jsonl`, `gap_labels.B.template.jsonl`,
   same for novelty).
2. Adjudicator resolves disagreements into
   `adjudication.template.jsonl`, preserving A, B, disagreement flag,
   adjudicated/final label, and dissent note.
3. Only `final_label` from the adjudicated record becomes
   `expected_labels` in frozen `cases/`. A/B trails are retained.

## Evidence requirements

Each single annotation carries: `evidence_refs`, `quoted_passages`,
`rationale`, `source_paper_ids`, `temporal_context`
(e.g. `pre-cutoff-2022`), and optional `confidence` (reported, never
scored automatically).

See `src/agentic_research/benchmarks/annotations.py` for the schema.
Agreement uses existing Phase 8 `evaluate_human_ratings`
(Cohen kappa + Krippendorff alpha) via `benchmarks/runner.py`.
