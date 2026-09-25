"""Quality checks for human annotation response files.

Validates shape, independence, and completeness. NEVER checks whether a
human answer agrees with Agentic-Research output -- agreement with the
system is NOT annotation quality.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .annotations import GAP_LABELS, NOVELTY_LABELS

# Phrases that would reveal system behavior to annotators. Response files
# and annotator-facing materials must not contain them.
LEAKAGE_PATTERNS: tuple[str, ...] = (
    "false disproof",
    "false survival",
    "false novelty",
    "should be",
    "must resolve",
    "predicted",
    "jaccard",
    "casefold",
    "alias table",
    "similarity score",
    "system verdict",
    "threshold",
)

CASE_ID_PATTERN = re.compile(r"^peft30v1-[A-Z]+-\d{3}$")

RETRIEVAL_LABEL = "relevant-list"


def allowed_labels(kind: str) -> tuple[str, ...]:
    if kind == "gap":
        return GAP_LABELS
    if kind == "novelty":
        return NOVELTY_LABELS
    if kind == "retrieval":
        return (RETRIEVAL_LABEL,)
    raise ValueError(f"Human annotation not defined for kind {kind!r}")


def validate_response_record(
    record: dict[str, object],
    *,
    expected_annotator: str,
    known_case_kinds: dict[str, str],
) -> list[str]:
    """Return problems for one response record (empty means valid)."""
    problems: list[str] = []
    case_id = record.get("case_id")
    if not isinstance(case_id, str) or not CASE_ID_PATTERN.match(case_id):
        problems.append(f"bad case_id {case_id!r}")
        return problems
    if case_id not in known_case_kinds:
        problems.append(f"unknown case {case_id!r}")
        return problems
    kind = known_case_kinds[case_id]
    annotator = record.get("annotator_id")
    if annotator != expected_annotator:
        problems.append(f"{case_id}: annotator {annotator!r} != {expected_annotator!r}")
    label = record.get("label")
    if label not in allowed_labels(kind):
        problems.append(f"{case_id}: invalid label {label!r} for kind {kind!r}")
    rationale = record.get("rationale")
    if not isinstance(rationale, str) or len(rationale.strip()) < 20:
        problems.append(f"{case_id}: rationale missing or too short")
    refs = record.get("evidence_refs")
    if not isinstance(refs, list) or not refs:
        problems.append(f"{case_id}: evidence_refs required")
    sources = record.get("source_paper_ids")
    if not isinstance(sources, list) or not sources:
        problems.append(f"{case_id}: source_paper_ids required")
    confidence = record.get("confidence")
    if confidence is not None and not (
        isinstance(confidence, int | float) and 0 <= confidence <= 1
    ):
        problems.append(f"{case_id}: confidence must be 0..1 or null")
    return problems


def validate_response_file(
    path: Path,
    *,
    expected_annotator: str,
    known_case_kinds: dict[str, str],
) -> list[str]:
    problems: list[str] = []
    seen: set[str] = set()
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        problems.append("response file is empty")
        return problems
    for index, line in enumerate(lines, start=1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            problems.append(f"line {index}: invalid JSON")
            continue
        if not isinstance(record, dict):
            problems.append(f"line {index}: record must be an object")
            continue
        case_id = str(record.get("case_id"))
        if case_id in seen:
            problems.append(f"duplicate case_id {case_id!r}")
        seen.add(case_id)
        problems.extend(
            validate_response_record(
                record,
                expected_annotator=expected_annotator,
                known_case_kinds=known_case_kinds,
            )
        )
    missing = set(known_case_kinds) - seen
    if missing:
        problems.append(f"missing cases: {sorted(missing)}")
    return problems


def scan_text_for_leakage(text: str) -> list[str]:
    lowered = text.casefold()
    return [pattern for pattern in LEAKAGE_PATTERNS if pattern in lowered]


def scan_file_for_leakage(path: Path) -> list[str]:
    return scan_text_for_leakage(path.read_text(encoding="utf-8"))
