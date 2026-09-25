# Adjudication guide (sci-bench-peft30-v1)

You receive the completed `annotator_A.jsonl` and
`annotator_B.jsonl` ONLY after both annotators have submitted.
You do not annotate cases yourself first.

## Procedure

1. **Compare independently**: for each case, place label A and label
   B side by side. Set `disagreement = (A != B)`.
2. **Agreements**: verify the shared label against the cited
   evidence (spot-check quotes/sections). If the evidence does not
   support the agreed label, say so in the adjudication rationale —
   do not silently change it; record dissent and set the final label
   to what the evidence supports.
3. **Disagreements**: read both rationales and the cited papers.
   Examine the evidence yourself (evidence index + frozen corpus).
4. **Determine** `adjudicated_label` (must be a valid rubric label
   for the case kind) and set `final_label` to it.
5. **Preserve dissent**: if either annotator's reading has merit,
   record it in `dissent_note`. Never delete or overwrite the
   original A/B records.
6. **Adjudication rationale**: cite the decisive evidence
   (paper/section/quote) and the rubric clause applied.

## Output

One JSON object per case in `adjudication.jsonl`, following
`src/agentic_research/benchmarks/annotations.py`
(`AdjudicatedAnnotation`): case_id, kind, annotation_a,
annotation_b, disagreement, adjudicator_id, adjudicated_label,
final_label, dissent_note (or null).

Only `final_label` becomes benchmark truth. The A/B trail is
retained permanently.
