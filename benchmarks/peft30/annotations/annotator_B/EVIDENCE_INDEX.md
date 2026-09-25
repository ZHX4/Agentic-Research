# PEFT-30 evidence index (sci-bench-peft30-v1)

Frozen manifest: `benchmarks/peft30/manifest.json` (N=30, cutoff
2022-12-31). PDFs live in `benchmarks/peft30/corpus/<id>.pdf`.
Metadata-only papers: title + abstract + year from the manifest.

No scientific conclusions are stated here — only locations.

## Full-text papers (14)

| paper_id | year | pages | title |
|---|---|---|---|
| peft30-001 | 2021 | 26 | LoRA: Low-Rank Adaptation of Large Language Models |
| peft30-002 | 2020 | 9 | AdapterHub: A Framework for Adapting Transformers |
| peft30-004 | 2021 | 15 | Prefix-Tuning: Optimizing Continuous Prompts for Generation |
| peft30-005 | 2021 | 15 | The Power of Scale for Parameter-Efficient Prompt Tuning |
| peft30-008 | 2022 | 18 | ATTEMPT: Parameter-Efficient Multi-task Tuning via Attentional Mixtures of Soft Prompts |
| peft30-009 | 2022 | 16 | Inducer-tuning: Connecting Prefix-tuning and Adapter-tuning |
| peft30-010 | 2022 | 37 | On Robust Prefix-Tuning for Text Classification |
| peft30-020 | 2020 | 5 | An Open-Source LoRa Physical Layer Prototype on GNU Radio |
| peft30-021 | 2023 | 26 | QLoRA: Efficient Finetuning of Quantized LLMs |
| peft30-022 | 2023 | 25 | LoRA-FA: Memory-Efficient Low-Rank Adaptation |
| peft30-023 | 2023 | 15 | DeepFake-Adapter: Dual-Level Adapter for DeepFake Detection |
| peft30-024 | 2023 | 30 | LLaMA-Adapter: Efficient Fine-tuning with Zero-init Attention |
| peft30-025 | 2023 | 12 | A Rank Stabilization Scaling Factor for Fine-Tuning with LoRA |
| peft30-030 | 2024 | 19 | Accurate LoRA-Finetuning Quantization via Information Retention |

## Metadata-only papers (16)

| paper_id | year | title |
|---|---|---|
| peft30-003 | 2020 | MAD-X: An Adapter-Based Framework for Multi-Task Cross-Lingual Transfer |
| peft30-006 | 2021 | P-Tuning v2: Prompt Tuning Can Be Comparable to Fine-tuning Universally Across Scales and Tasks |
| peft30-007 | 2021 | AdapterDrop: On the Efficiency of Adapters in Transformers |
| peft30-011 | 2022 | Few-Shot Parameter-Efficient Fine-Tuning is Better and Cheaper than In-Context Learning |
| peft30-012 | 2022 | AdapterBias: Parameter-efficient Token-dependent Representation Shift |
| peft30-013 | 2022 | SparseAdapter: Improving the Parameter-Efficiency of Adapters |
| peft30-014 | 2022 | PPT: Pre-trained Prompt Tuning for Few-shot Learning |
| peft30-015 | 2022 | ST-Adapter: Parameter-Efficient Image-to-Video Transfer Learning |
| peft30-016 | 2022 | Conv-Adapter: Parameter Efficient Transfer Learning for ConvNets |
| peft30-017 | 2022 | PTR: Prompt Tuning with Rules for Text Classification |
| peft30-018 | 2022 | Pre-train, Prompt, and Predict: A Systematic Survey of Prompting Methods |
| peft30-019 | 2020 | Monolingual Adapters for Zero-Shot Neural Machine Translation |
| peft30-026 | 2023 | DyLoRA: Tuning with Dynamic Search-Free Low-Rank Adaptation |
| peft30-027 | 2023 | LQ-LoRA: Low-rank Plus Quantized Matrix Decomposition |
| peft30-028 | 2023 | LoftQ: LoRA-Fine-Tuning-Aware Quantization |
| peft30-029 | 2024 | DoRA: Weight-Decomposed Low-Rank Adaptation |

## How to locate evidence

- PDFs: open `corpus/<id>.pdf`; methods are usually sections 2–4,
  experiments/results sections 4–6, limitations near the end.
  Cite the PDF page number (e.g. `peft30-001:page:7`).
- Metadata-only: cite `paper_id:metadata` and quote the
  title/abstract wording from the manifest. Do not claim
  same-context verification from metadata alone.

## Per-case evidence map

- N-001: peft30-001 (PDF), peft30-020 (PDF)
- N-002: peft30-004 (PDF), peft30-010 (PDF)
- N-003: peft30-021 (PDF), peft30-027 (meta), peft30-028 (meta), peft30-030 (PDF)
- N-004: peft30-025 (PDF), peft30-026 (meta)
- N-005: peft30-001 (PDF), peft30-029 (meta)
- N-006: whole pre-cutoff corpus (search task)
- N-007: peft30-026 (meta)
- G-001: peft30-001 (PDF), peft30-004 (PDF), plus pre-cutoff search
- G-002: peft30-015 (meta)
- G-003: peft30-016 (meta)
- G-004: peft30-005 (PDF), peft30-006 (meta), peft30-010 (PDF), peft30-011 (meta)
- R-001: whole corpus (ranking task)
