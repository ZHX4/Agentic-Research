# Gap annotation rubric (sci-bench-peft30-v1)

Kind: `gap`. Allowed labels (exact strings):

## valid_opportunity

- **Definition**: the combination is substantively untested in the
  pre-cutoff corpus AND each component (method, dataset/task) is
  supported by ≥2 pre-cutoff papers AND the combination is a
  non-trivial scientific question (not a trivial cross-product).
- **Minimum evidence**: ≥2 supporting paper IDs with quotes showing
  each component; statement of what exact configuration is missing.
- **Disqualifying**: any pre-cutoff paper establishing the exact
  combination; component support from a single paper.
- **Record**: label, papers, quotes, missing-configuration statement,
  rationale + Uncertainty note.

## already_addressed

- **Definition**: a pre-cutoff paper establishes the exact
  method/dataset/task combination in the same context.
- **Minimum evidence**: paper ID + section/page + verbatim quote
  showing method, dataset/task, and result.
- **Record**: as above.

## partially_addressed

- **Definition**: adjacent work touches the combination (shared
  method family, adjacent dataset/task, or ablation) but leaves the
  exact configuration untested.
- **Minimum evidence**: what was shown (quote) + precise statement
  of what remains untested.
- **Record**: as above.

## ambiguous

- **Definition**: the candidate is underspecified (entities unclear,
  e.g. "efficient tuning" without a method) or the evidence is
  genuinely uninterpretable. No verdict possible either way.
- **Minimum evidence**: statement of what is underspecified and why
  no label fits.
- **Record**: label + rationale (evidence refs optional but welcome).

## unsupported

- **Definition**: the candidate is a corpus-sparsity artifact
  (components appear in <2 pre-cutoff papers), rests on extraction
  error, or is scientifically trivial.
- **Minimum evidence**: support counts + reason (sparsity / error /
  triviality).
- **Record**: as above.

**"I didn't find it" → `unsupported` or `ambiguous`, never
`valid_opportunity`.** Opportunity requires positive component
support, not just absence.
