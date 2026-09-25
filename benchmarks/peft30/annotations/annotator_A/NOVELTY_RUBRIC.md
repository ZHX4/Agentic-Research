# Novelty annotation rubric (sci-bench-peft30-v1)

Kind: `novelty`. Allowed labels (exact strings):

## direct_prior

- **Definition**: a pre-cutoff paper establishes the exact
  method/dataset/task combination in the same local context.
- **Minimum evidence**: paper ID + section/page + verbatim quote with
  method, dataset/task, and result. Year must be ≤2022.

## near_equivalent

- **Definition**: different name, surface form, or minor variant, but
  the SAME scientific claim is already established pre-cutoff
  (e.g. a paper describing "low-rank adaptation" that is
  mechanistically the claimed method; an indirect paper whose
  composition establishes the combination).
- **Minimum evidence**: equivalence justification (mechanism,
  configuration, claim overlap) + quotes from both sides. Name
  similarity alone is NOT enough; name difference alone does NOT
  rule it out.

## related_not_disqualifying

- **Definition**: same family but materially different scientific
  configuration. Examples that do NOT automatically disqualify:
  - **rank changes** (e.g. rank 8 vs 64 with different claims);
  - **quantization changes** (4-bit QLoRA vs fp16 LoRA are different
    techniques even though both are "quantized LoRA");
  - **different dataset or task**;
  - **different mechanism** (e.g. weight-decomposed vs standard
    low-rank update).
- **Minimum evidence**: what is shared + what is materially
  different (quotes).

## no_disqualifying_found

- **Definition**: a diligent search of the pre-cutoff corpus
  (title/abstract/full text where available) found no direct or near
  prior work. List what was checked.
- **Minimum evidence**: papers examined + why each fails to
  disqualify.

## insufficient_evidence

- **Definition**: the verdict cannot be reached from accessible
  evidence: metadata-only related work, unparsable artifacts, or
  contradictory fragments. Applies when the ONLY related records
  lack full text.
- **Minimum evidence**: which records are missing and what would be
  needed.

## Worked distinctions

- **LoRA vs "low-rank adaptation"**: decide by mechanism described
  in the methods, never by the name. Document the mechanism match.
- **QLoRA vs LoRA**: different techniques (quantization +
  training regime). A QLoRA paper does not disqualify a LoRA claim
  by name overlap, nor vice versa.
- **Same family ≠ same work. Different name ≠ different work.**
  Every equivalence verdict needs a scientific justification.
