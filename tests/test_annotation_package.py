"""Annotation-package integrity tests (no human answers exist yet).

Pins: clean-case neutrality, blank templates, A/B separation, leakage
absence, response validation behavior, and frozen-corpus preservation.
These tests never compare human answers to system output.
"""

from __future__ import annotations

import json
from pathlib import Path

from agentic_research.benchmarks.annotation_qc import (
    allowed_labels,
    scan_file_for_leakage,
    validate_response_file,
)

BASE = Path("benchmarks/peft30/annotations")
ROOT = Path(__file__).resolve().parent.parent


def load_clean() -> list[dict[str, object]]:
    raw: object = json.loads((BASE / "cases.clean.json").read_text(encoding="utf-8"))
    assert isinstance(raw, list)
    return [dict(item) for item in raw if isinstance(item, dict)]


def human_kinds() -> dict[str, str]:
    kinds: dict[str, str] = {}
    for case in load_clean():
        if case.get("human_label") is True:
            case_id = case.get("case_id")
            kind = case.get("kind")
            assert isinstance(case_id, str) and isinstance(kind, str)
            kinds[case_id] = kind
    return kinds


def frozen_paper_ids() -> set[str]:
    raw: object = json.loads((ROOT / "benchmarks/peft30/manifest.json").read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    papers = raw.get("papers")
    assert isinstance(papers, list)
    ids: set[str] = set()
    for paper in papers:
        assert isinstance(paper, dict)
        paper_id = paper.get("paper_id")
        assert isinstance(paper_id, str)
        ids.add(paper_id)
    return ids


def test_clean_cases_grounded_and_neutral() -> None:
    cases = load_clean()
    assert len(cases) == 14
    human = [c for c in cases if c.get("human_label") is True]
    assert len(human) == 12
    papers = frozen_paper_ids()
    for case in cases:
        assert "case_id" in case and "question" in case and "kind" in case
        assert "expected_label" not in case
        related = case.get("related_paper_ids")
        assert isinstance(related, list)
        for paper_id in related:
            assert isinstance(paper_id, str)
            assert paper_id in papers, paper_id


def test_response_templates_blank_and_separated() -> None:
    kinds = human_kinds()
    rows_a = [
        json.loads(line)
        for line in (BASE / "annotator_A.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    rows_b = [
        json.loads(line)
        for line in (BASE / "annotator_B.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(rows_a) == len(rows_b) == len(kinds) == 12
    assert [r["case_id"] for r in rows_a] == [r["case_id"] for r in rows_b]
    assert [r["question"] for r in rows_a] == [r["question"] for r in rows_b]
    for record in rows_a + rows_b:
        assert record["label"] is None
        assert record["rationale"] == ""
        assert record["evidence_refs"] == []
    assert {r["annotator_id"] for r in rows_a} == {"annotator-a"}
    assert {r["annotator_id"] for r in rows_b} == {"annotator-b"}


def test_no_leakage_in_annotator_package() -> None:
    checked = 0
    for path in BASE.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".json", ".jsonl"}:
            continue
        if "adjudication.template" in path.name:
            continue
        assert scan_file_for_leakage(path) == [], path
        checked += 1
    assert checked >= 10


def test_per_party_packages_isolated() -> None:
    a_files = {p.name for p in (BASE / "annotator_A").iterdir()}
    b_files = {p.name for p in (BASE / "annotator_B").iterdir()}
    assert "response_template.jsonl" in a_files and "response_template.jsonl" in b_files
    assert "ADJUDICATION_GUIDE.md" not in a_files | b_files
    adjudicator_files = {p.name for p in (BASE / "adjudicator").iterdir()}
    assert adjudicator_files == {"ADJUDICATION_GUIDE.md"}


def test_blank_template_fails_validation() -> None:
    problems = validate_response_file(
        BASE / "annotator_A.jsonl",
        expected_annotator="annotator-a",
        known_case_kinds=human_kinds(),
    )
    assert any("rationale" in p or "evidence_refs" in p or "label" in p for p in problems)


def test_cross_annotator_contamination_fails() -> None:
    problems = validate_response_file(
        BASE / "annotator_A.jsonl",
        expected_annotator="annotator-b",
        known_case_kinds=human_kinds(),
    )
    assert any("annotator-b" in p for p in problems)


def test_filled_dev_record_passes_and_dupes_fail(tmp_path: Path) -> None:
    kinds = human_kinds()
    first_case = sorted(kinds)[0]
    record = {
        "case_id": first_case,
        "annotator_id": "annotator-a",
        "label": allowed_labels(kinds[first_case])[0],
        "evidence_refs": ["peft30-001:page:7"],
        "quoted_passages": ["a short verbatim quote"],
        "source_paper_ids": ["peft30-001"],
        "rationale": "A sufficiently long dev rationale with Uncertainty: none.",
        "temporal_context": "pre-cutoff-2022",
        "confidence": 0.7,
    }
    single = tmp_path / "single.jsonl"
    single.write_text(json.dumps(record) + "\n", encoding="utf-8")
    assert (
        validate_response_file(
            single,
            expected_annotator="annotator-a",
            known_case_kinds={first_case: kinds[first_case]},
        )
        == []
    )
    dupe = tmp_path / "dupe.jsonl"
    dupe.write_text(json.dumps(record) + "\n" + json.dumps(record) + "\n", encoding="utf-8")
    assert any(
        "duplicate" in p
        for p in validate_response_file(
            dupe,
            expected_annotator="annotator-a",
            known_case_kinds={first_case: kinds[first_case]},
        )
    )


def test_unknown_case_rejected(tmp_path: Path) -> None:
    bad = tmp_path / "bad.jsonl"
    bad.write_text(
        json.dumps(
            {
                "case_id": "peft30v1-X-999",
                "annotator_id": "annotator-a",
                "label": "valid_opportunity",
                "evidence_refs": ["x"],
                "source_paper_ids": ["peft30-001"],
                "rationale": "long enough dev rationale text here",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    problems = validate_response_file(
        bad, expected_annotator="annotator-a", known_case_kinds=human_kinds()
    )
    assert any("unknown case" in p for p in problems)


def test_frozen_corpus_unchanged() -> None:
    import sys

    sys.path.insert(0, "src")
    from agentic_research.benchmarks.manifest import CorpusManifest, validate_manifest

    manifest = CorpusManifest.model_validate(
        json.loads((ROOT / "benchmarks/peft30/manifest.json").read_text(encoding="utf-8"))
    )
    assert manifest.status == "frozen"
    assert len(manifest.papers) == 30
    assert validate_manifest(manifest, corpus_root=ROOT / "benchmarks/peft30/corpus") == []
