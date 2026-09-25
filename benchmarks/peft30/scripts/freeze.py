"""Freeze sci-bench-peft30-v1 from a draft manifest.

Usage (PowerShell):
  python benchmarks/peft30/scripts/freeze.py --input <draft.json> --output <frozen.json>

Refuses invalid manifests and refuses to overwrite a different frozen
snapshot. Idempotent when content is identical.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")

from agentic_research.benchmarks.manifest import (  # noqa: E402
    CorpusManifest,
    freeze_manifest,
    validate_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze PEFT-30 manifest")
    parser.add_argument("--input", required=True, help="Draft manifest JSON path")
    parser.add_argument("--output", required=True, help="Frozen manifest output path")
    parser.add_argument("--corpus-root", default=None, help="Corpus directory for artifact checks")
    args = parser.parse_args()

    draft = CorpusManifest.model_validate(json.loads(Path(args.input).read_text(encoding="utf-8")))
    root = Path(args.corpus_root) if args.corpus_root else None
    problems = validate_manifest(draft, corpus_root=root)
    if problems:
        print("INVALID: " + "; ".join(problems))
        return 1
    freeze_manifest(draft, Path(args.output), corpus_root=root)
    print(f"frozen -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
