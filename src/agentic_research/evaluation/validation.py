"""Dataset and split-integrity validation for Phase 8 benchmarks."""
from __future__ import annotations

from collections import defaultdict

from agentic_research.schemas.phase8 import BenchmarkCase


def validate_split_disjointness(splits: dict[str, list[BenchmarkCase]]) -> None:
    case_to_splits: dict[str, set[str]] = defaultdict(set)
    hash_to_splits: dict[str, set[str]] = defaultdict(set)
    for split, cases in splits.items():
        seen_ids: set[str] = set()
        seen_hashes: set[str] = set()
        for case in cases:
            if case.case_id in seen_ids:
                raise ValueError(f"Duplicate case_id {case.case_id!r} within split {split!r}")
            if case.input_hash in seen_hashes:
                raise ValueError(f"Duplicate input_hash within split {split!r}")
            seen_ids.add(case.case_id); seen_hashes.add(case.input_hash)
            case_to_splits[case.case_id].add(split); hash_to_splits[case.input_hash].add(split)
    leaked_cases = {case_id: names for case_id, names in case_to_splits.items() if len(names) > 1}
    leaked_inputs = {input_hash: names for input_hash, names in hash_to_splits.items() if len(names) > 1}
    if leaked_cases:
        raise ValueError(f"Case IDs overlap across splits: {sorted(leaked_cases)}")
    if leaked_inputs:
        raise ValueError(f"Input hashes overlap across splits: {sorted(leaked_inputs)}")
