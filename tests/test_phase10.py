from __future__ import annotations

from pathlib import Path

import pytest

from agentic_research.publication.engine import (
    audit_licenses,
    build_artifact_entry,
    build_benchmark_paper,
    build_case_study,
    build_publication_bundle,
    build_reproducibility_package,
)
from agentic_research.schemas.phase10 import Manuscript, ModelProviderDisclosure, PublicationSection


def test_artifact_hash_is_computed_from_file(tmp_path: Path) -> None:
    path = tmp_path / "artifact.txt"
    path.write_text("hello", encoding="utf-8")
    entry = build_artifact_entry(path, "result", "r1", "MIT")
    assert len(entry.sha256) == 64
    assert entry.size_bytes == 5


def test_unknown_license_requires_review(tmp_path: Path) -> None:
    path = tmp_path / "artifact.txt"
    path.write_text("hello", encoding="utf-8")
    entry = build_artifact_entry(path, "result", "r1")
    package = build_reproducibility_package("abcdef123456789", [entry], "pyproject.toml", ["pytest -q"])
    audit = audit_licenses(package.artifacts)
    assert audit[0].status == "review"


def test_ready_manuscript_requires_evidence() -> None:
    with pytest.raises(ValueError):
        Manuscript(
            manuscript_id="m1",
            kind="system_paper",
            title="T",
            abstract="A",
            sections=[PublicationSection(title="S", markdown="M")],
            status="ready",
        )


def test_case_study_requires_pipeline_fields() -> None:
    with pytest.raises(ValueError):
        build_case_study({"case_id": "c1"})


def _ready_inputs(tmp_path: Path):
    path = tmp_path / "artifact.txt"
    path.write_text("hello", encoding="utf-8")
    entry = build_artifact_entry(path, "result", "r1", "MIT")
    package = build_reproducibility_package("abcdef123456789", [entry], "pyproject.toml", ["pytest -q"])
    disclosure = [
        ModelProviderDisclosure(
            provider="test",
            model="model",
            role="generation",
            local_or_remote="local",
            training_data_disclosed=False,
            usage_notes="Synthetic test disclosure.",
        )
    ]
    architecture = {"evidence_refs": ["arch:1"]}
    evaluation = {"provenance_refs": ["bench:1"], "benchmarks": [{"benchmark_id": "b1", "metric": 0.9}]}
    case = {
        "case_id": "c1",
        "hypothesis": {"id": "h1"},
        "verification": {"id": "v1"},
        "execution": {"id": "e1"},
        "evaluation": {"id": "ev1"},
        "provenance_refs": ["case:1"],
    }
    return architecture, evaluation, case, disclosure, package


def test_ready_bundle_is_emittable_with_evidence_disclosure_and_passed_licenses(tmp_path: Path) -> None:
    architecture, evaluation, case, disclosure, package = _ready_inputs(tmp_path)
    bundle = build_publication_bundle("abcdef123456789", architecture, evaluation, case, disclosure, package)
    assert bundle.status == "ready"
    assert {item.kind for item in bundle.manuscripts} == {"system_paper", "benchmark_paper", "case_study"}
    assert all(item.status == "pass" for item in bundle.license_audit)


def test_bundle_is_blocked_when_disclosure_is_missing(tmp_path: Path) -> None:
    architecture, evaluation, case, _disclosure, package = _ready_inputs(tmp_path)
    bundle = build_publication_bundle("abcdef123456789", architecture, evaluation, case, [], package)
    assert bundle.status == "blocked"
    assert any("disclosure" in warning.lower() for warning in bundle.warnings)


def test_benchmark_paper_is_blocked_without_results() -> None:
    manuscript = build_benchmark_paper({"provenance_refs": ["bench:1"], "benchmarks": []})
    assert manuscript.status == "blocked"


def test_bundle_rejects_stale_artifact_manifest(tmp_path: Path) -> None:
    architecture, evaluation, case, disclosure, package = _ready_inputs(tmp_path)
    artifact_path = Path(package.artifacts[0].path)
    artifact_path.write_text("tampered", encoding="utf-8")
    with pytest.raises(ValueError, match="Artifact hash mismatch"):
        build_publication_bundle("abcdef123456789", architecture, evaluation, case, disclosure, package)


def test_license_audit_coverage_matches_exact_artifact_set(tmp_path: Path) -> None:
    from agentic_research.publication.engine import validate_license_audit_coverage
    path = tmp_path / "artifact.txt"
    path.write_text("hello", encoding="utf-8")
    entry = build_artifact_entry(path, "result", "r1", "MIT")
    audits = audit_licenses([entry])
    validate_license_audit_coverage([entry], audits)
