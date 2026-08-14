"""Phase 10 publication bundle builder."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agentic_research.schemas.phase10 import (
    ArtifactManifestEntry,
    LicenseAuditEntry,
    Manuscript,
    ModelProviderDisclosure,
    PublicationBundle,
    PublicationSection,
    ReproducibilityPackage,
)

PERMISSIVE_SPDX = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "CC0-1.0", "Unlicense"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _evidence_refs(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return []
    refs = payload.get("provenance_refs", payload.get("evidence_refs", []))
    return sorted({str(item) for item in refs}) if isinstance(refs, list) else []


def _section(title: str, markdown: str, refs: list[str]) -> PublicationSection:
    return PublicationSection(title=title, markdown=markdown.strip(), evidence_refs=refs)


def build_system_paper(source_commit: str, architecture: dict[str, Any]) -> Manuscript:
    refs = _evidence_refs(architecture)
    sections = [
        _section("1. Introduction", "This manuscript describes Agentic-Research as an evidence-grounded scientific research-agent system. It separates literature acquisition, evidence extraction, retrieval, gap discovery, adversarial novelty verification, hypothesis reasoning, scientific execution, evaluation, and autonomous control into auditable stages.", refs),
        _section("2. System architecture", "```text\nLiterature → Evidence → World Model → Gaps → Novelty → Hypotheses → Experiments → Evaluation → Autonomous Control\n```\nEach stage communicates through explicit schemas and persisted artifacts rather than hidden conversational state.", refs),
        _section("3. Scientific safeguards", "The system uses provenance references, deterministic identifiers, temporal cutoffs, adversarial novelty verification, falsification criteria, reproducible execution manifests, sandboxing, benchmark contamination checks, and stage-specific review.", refs),
        _section("4. Reproducibility and limitations", f"The publication artifact is tied to source commit `{source_commit}`. Results must be interpreted within the configured literature coverage, benchmark coverage, search budget, and execution environment; the system must not convert bounded search failure into a claim of global novelty.", refs),
    ]
    abstract = "Agentic-Research is an evidence-grounded autonomous research-agent architecture designed to discover, challenge, execute, and evaluate scientific hypotheses while preserving provenance and reproducibility across stages."
    status = "ready" if refs else "blocked"
    return Manuscript(manuscript_id=f"system-paper:{source_commit[:12]}", kind="system_paper", title="Agentic-Research: An Evidence-Grounded Autonomous Scientific Research System", abstract=abstract, sections=sections, evidence_refs=refs, status=status)


def build_benchmark_paper(evaluation_report: dict[str, Any]) -> Manuscript:
    refs = _evidence_refs(evaluation_report)
    summary = evaluation_report.get("benchmarks", []) if isinstance(evaluation_report, dict) else []
    sections = [
        _section("1. Benchmark design", "This benchmark evaluates the research-agent pipeline at retrieval, extraction, gap discovery, novelty verification, temporal integrity, human assessment, baseline comparison, ablation, and cost/compute levels.", refs),
        _section("2. Evaluation protocol", "All benchmark inputs should be frozen before reporting. Train/dev/test contamination is rejected by case identifier and input hash; prediction coverage is validated before metrics are computed.", refs),
        _section("3. Results", "```json\n" + json.dumps(summary, indent=2, ensure_ascii=False) + "\n```", refs),
        _section("4. Interpretation", "Reported metrics describe the measured benchmark conditions only. They do not establish universal scientific superiority or global novelty.", refs),
    ]
    return Manuscript(manuscript_id="benchmark-paper:generated", kind="benchmark_paper", title="Evaluating Agentic-Research: Retrieval, Evidence, Gap Discovery, Novelty, and Execution Benchmarks", abstract="A benchmark-oriented evaluation of the evidence-grounded research-agent pipeline under controlled, reproducible evaluation conditions.", sections=sections, evidence_refs=refs, status="ready" if refs else "blocked")


def build_case_study(case_payload: dict[str, Any]) -> Manuscript:
    refs = _evidence_refs(case_payload)
    required = ["case_id", "hypothesis", "verification", "execution", "evaluation"]
    missing = [key for key in required if key not in case_payload]
    if missing:
        raise ValueError(f"Case study missing required fields: {missing}")
    sections = [
        _section("1. Discovery provenance", json.dumps(case_payload.get("verification"), indent=2, ensure_ascii=False), refs),
        _section("2. Hypothesis", json.dumps(case_payload.get("hypothesis"), indent=2, ensure_ascii=False), refs),
        _section("3. Experimental execution", json.dumps(case_payload.get("execution"), indent=2, ensure_ascii=False), refs),
        _section("4. Evaluation", json.dumps(case_payload.get("evaluation"), indent=2, ensure_ascii=False), refs),
        _section("5. Limitations", json.dumps(case_payload.get("limitations", []), indent=2, ensure_ascii=False), refs),
    ]
    status = "ready" if refs else "blocked"
    return Manuscript(manuscript_id=f"case-study:{case_payload['case_id']}", kind="case_study", title=f"Validated Discovery Case Study: {case_payload['case_id']}", abstract="A provenance-backed case study tracing a candidate gap through adversarial verification, hypothesis reasoning, experiment execution, and evaluation.", sections=sections, evidence_refs=refs, status=status)


def build_artifact_entry(path: Path, kind: str, artifact_id: str, license_spdx: str | None = None, source: str | None = None) -> ArtifactManifestEntry:
    if not path.is_file():
        raise ValueError(f"Artifact does not exist: {path}")
    return ArtifactManifestEntry(artifact_id=artifact_id, path=str(path), kind=kind, sha256=sha256_file(path), size_bytes=path.stat().st_size, license_spdx=license_spdx, source=source)


def audit_licenses(artifacts: list[ArtifactManifestEntry]) -> list[LicenseAuditEntry]:
    results: list[LicenseAuditEntry] = []
    for artifact in artifacts:
        spdx = artifact.license_spdx
        if not spdx:
            status, reason = "review", "No SPDX license identifier supplied; manual verification required."
        elif spdx in PERMISSIVE_SPDX:
            status, reason = "pass", f"SPDX {spdx} is in the configured permissive-license allowlist; verify attribution and venue-specific requirements separately."
        else:
            status, reason = "review", f"SPDX {spdx} is not in the configured automatic-pass allowlist; manual compatibility review required."
        results.append(LicenseAuditEntry(artifact_id=artifact.artifact_id, license_spdx=spdx, source=artifact.source, status=status, reason=reason))
    return results


def build_reproducibility_package(source_commit: str, artifacts: list[ArtifactManifestEntry], environment_lock: str, commands: list[str], notes: list[str] | None = None) -> ReproducibilityPackage:
    digest = hashlib.sha256(json.dumps([item.model_dump(mode="json") for item in artifacts], sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return ReproducibilityPackage(package_id=f"repro:{source_commit[:12]}:{digest}", created_at=datetime.now(timezone.utc).isoformat(), source_commit=source_commit, artifacts=artifacts, environment_lock=environment_lock, reproduction_commands=commands, notes=notes or [])


def build_publication_bundle(source_commit: str, architecture: dict[str, Any], evaluation_report: dict[str, Any], case_study: dict[str, Any], disclosure: list[ModelProviderDisclosure], reproducibility: ReproducibilityPackage) -> PublicationBundle:
    manuscripts = [build_system_paper(source_commit, architecture), build_benchmark_paper(evaluation_report), build_case_study(case_study)]
    audits = audit_licenses(reproducibility.artifacts)
    blocking = [item for item in manuscripts if item.status != "ready"] + [item for item in audits if item.status != "pass"]
    status = "blocked" if blocking else "ready"
    warnings = ["Publication bundle remains non-ready until every manuscript has evidence and every artifact has an audited license."] if blocking else []
    bundle_id = hashlib.sha256(json.dumps({"source_commit": source_commit, "manuscripts": [m.model_dump(mode="json") for m in manuscripts], "artifacts": [a.model_dump(mode="json") for a in reproducibility.artifacts]}, sort_keys=True).encode("utf-8")).hexdigest()[:20]
    return PublicationBundle(bundle_id=f"publication:{bundle_id}", status=status, manuscripts=manuscripts, disclosure=disclosure, license_audit=audits, reproducibility=reproducibility, warnings=warnings)
