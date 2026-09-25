# PEFT-30 Annotator Guide (sci-bench-peft30-v1)

## Purpose

You are judging whether candidate research opportunities and novelty
claims in parameter-efficient fine-tuning (PEFT) are supported by a
frozen corpus of 30 real papers. Your labels become the benchmark
truth that an AI research system will later be measured against.

## Temporal cutoff: 2022-12-31

- A paper dated **2022 or earlier** may support or disqualify a claim.
- A paper dated **2023 or later** must NEVER disqualify a pre-cutoff
  claim. If a case says "pre-cutoff only", ignore later papers
  entirely, even if they settle the question.
- Record the publication year of every paper you rely on.

## Independence (binding)

- Annotators A and B work independently. Do not communicate about
  cases, labels, or evidence before both submissions are collected.
- Judge each case from the papers, not from memory of later work.

## Two mandatory rules

**"Do not use the current Agentic-Research behavior as a reference
answer."** You have not seen its output and must not seek it.

**"Absence of evidence in this corpus is not automatically evidence
of a valid research opportunity."** A combination can be absent
because the corpus is small (30 papers), because extraction is
imperfect, or because the idea is uninteresting — not because it is
a discovery. See `GAP_RUBRIC.md` (`unsupported`).

## Evidence requirements (every case)

- `source_paper_ids`: frozen IDs (e.g. `peft30-001`).
- `evidence_refs`: `paper_id:section-or-page` (e.g.
  `peft30-001:section:3`, `peft30-021:page:5`). For PDFs use the page
  number of the PDF file; for metadata-only records use
  `paper_id:metadata` plus title/abstract wording.
- `quoted_passages`: short verbatim quotes (≤40 words each).
- `rationale`: why the label fits (≥1 paragraph). End with an
  `Uncertainty:` note stating what could change your mind.
- `confidence`: 0..1 (reported only; never auto-scored).

No label without a rationale. No rationale without evidence.

## Citing papers

Frozen manifest: `benchmarks/peft30/manifest.json`. PDFs:
`benchmarks/peft30/corpus/<paper_id>.pdf` (14 papers; see
`EVIDENCE_INDEX.md` for page counts). The other 16 are
metadata-only: title + abstract + year only.

## Key distinctions

- **Direct prior vs near-equivalent** (novelty): direct = same
  method + same dataset/task in the same context, pre-cutoff.
  Near-equivalent = different name or minor variant, but the same
  scientific claim already established. Justify equivalence
  scientifically (mechanism, configuration, claim) — see
  `NOVELTY_RUBRIC.md`.
- **Related vs disqualifying**: same family (e.g. two quantized-LoRA
  variants) is NOT automatically disqualifying. Different rank,
  quantization, dataset, or task can be a materially different claim.
- **Metadata-only**: you cannot verify same-context claims from a
  title/abstract. Use `insufficient_evidence` (novelty) or weigh
  toward `unsupported`/`ambiguous` (gap) — see rubrics.
- **Terminology variants**: LoRA / low-rank adaptation, prefix-tuning
  / prefix tuning, adapter / AdapterHub may or may not denote the
  same thing. Read the method sections; never decide by name alone.
  Beware homographs: similar names can denote unrelated work.
- **Contradictions**: two papers reporting opposite results may both
  be right under different conditions (model, scale, task). Compare
  conditions before calling a genuine contradiction.
- **Corpus sparsity**: with 30 papers, most combinations are absent.
  Absence + thin component support (1–2 papers) means `unsupported`,
  not an opportunity.

## Retrieval case (peft30v1-R-001)

Set `label` to exactly `relevant-list` and put your ranked relevant
paper IDs (most relevant first) in `source_paper_ids`. Relevance =
the paper's title/abstract (or full text) substantively concerns the
query. Note borderline calls in the rationale.

## Temporal cases (peft30v1-T-001/T-002)

Not assigned to annotators. They are executed by the benchmark
runner to check cutoff enforcement.
