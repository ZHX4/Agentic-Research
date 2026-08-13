"""Benchmark split-integrity validation."""
from __future__ import annotations

from collections import defaultdict

from agentic_research.schemas.phase8 import BenchmarkCase


def validate_split_disjointness(splits: dict[str, list[BenchmarkCase]]) -> None:
    """Reject case-ID or input-hash overlap across named benchmark splits."""
    seen_ids: dict[str, str] = {}
    seen_hashes: dict[str, str] = {}
    for split_name, cases in splits.items():
        local_ids: set[str] = set()
        local_hashes: set[str] = set()
        for case in cases:
            if case.case_id in local_ids:
                raise ValueError(f"Duplicate case_id within split {split_name!r}: {case.case_id}")
            if case.input_hash in local_hashes:
                raise ValueError(f"Duplicate input_hash within split {split_name!r}: {case.input_hash}")
            local_ids.add(case.case_id)
            local_hashes.add(case.input_hash)
            prior_split = seen_ids.get(case.case_id)
            if prior_split is not None and prior_split != split_name:
                raise ValueError(f"case_id {case.case_id!r} appears in both {prior_split!r} and {split_name!r}")
            prior_hash_split = seen_hashes.get(case.input_hash)
            if prior_hash_split is not None and prior_hash_split != split_name:
                raise ValueError(f"input_hash {case.input_hash!r} appears in both {prior_hash_split!r} and {split_name!r}")
        for case_id in local_ids:
            seen_ids[case_id] = split_name
        for input_hash in local_hashes:
            seen_hashes[input_hash] = split_name


def case_counts(splits: dict[str, list[BenchmarkCase]]) -> dict[str, int]:
    return {name: len(cases) for name, cases in sorted(splits.items())}
