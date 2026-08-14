from __future__ import annotations

from pathlib import Path

import pytest

from agentic_research.publication.engine import build_artifact_entry, build_case_study, build_publication_bundle, build_reproducibility_package
from agentic_research.schemas.phase10 import ArtifactManifestEntry, Manuscript, PublicationSection, ModelProviderDisclosure


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
    from agentic_research.publication.engine import audit_licenses
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


def test_ready_bundle_requires_disclosure_and_passed_licenses(tmp_path: Path) -> None:
    path = tmp_path / "artifact.txt"
    path.write_text("hello", encoding="utf-8")
    entry = build_artifact_entry(path, "result", "r1", "MIT")
    package = build_reproducibility_package("abcdef123456789", [entry], "pyproject.toml", ["pytest -q"])
    disclosure = [ModelProviderDisclosure(provider="test", model="model", role="generation", local_or_remote="local", training_data_disclosed=False, usage_notes="Synthetic test disclosure.")]
    with pytest.raises(ValueError):
        build_publication_bundle("abcdef123456789", {"evidence_refs": ["arch:1"]}, {"provenance_refs": ["bench:1"]}, {"case_id": "c1", "hypothesis": {}, "verification": {}, "execution": {}, "evaluation": {}, "provenance_refs": ["case:1"]}, disclosure, package)
