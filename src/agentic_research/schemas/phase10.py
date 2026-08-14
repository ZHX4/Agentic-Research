"""Phase 10 publication and release contracts."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PublicationStatus = Literal["draft", "ready", "blocked"]
LicenseStatus = Literal["pass", "review", "fail"]
ArtifactKind = Literal["code", "dataset", "config", "result", "manuscript", "environment", "other"]


class ArtifactManifestEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(min_length=1)
    path: str = Field(min_length=1)
    kind: ArtifactKind
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)
    license_spdx: str | None = None
    source: str | None = None


class ModelProviderDisclosure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    version_or_revision: str | None = None
    role: str = Field(min_length=1)
    local_or_remote: Literal["local", "remote"]
    training_data_disclosed: bool
    usage_notes: str = Field(min_length=1)


class LicenseAuditEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(min_length=1)
    license_spdx: str | None = None
    source: str | None = None
    status: LicenseStatus
    reason: str = Field(min_length=1)


class PublicationSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    markdown: str = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)


class Manuscript(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manuscript_id: str = Field(min_length=1)
    kind: Literal["system_paper", "benchmark_paper", "case_study"]
    title: str = Field(min_length=1)
    abstract: str = Field(min_length=1)
    sections: list[PublicationSection] = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    status: PublicationStatus

    @model_validator(mode="after")
    def validate_ready(self) -> "Manuscript":
        if self.status == "ready" and not self.evidence_refs:
            raise ValueError("Ready manuscripts require evidence_refs")
        if self.status == "ready" and any(not section.evidence_refs for section in self.sections):
            raise ValueError("Ready manuscripts require evidence references on every section")
        return self


class ReproducibilityPackage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(min_length=1)
    created_at: str = Field(min_length=1)
    source_commit: str = Field(pattern=r"^[0-9a-f]{7,64}$")
    artifacts: list[ArtifactManifestEntry] = Field(min_length=1)
    environment_lock: str = Field(min_length=1)
    reproduction_commands: list[str] = Field(min_length=1)
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique(self) -> "ReproducibilityPackage":
        ids = [item.artifact_id for item in self.artifacts]
        if len(ids) != len(set(ids)):
            raise ValueError("Artifact IDs must be unique")
        return self


class PublicationBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(min_length=1)
    status: PublicationStatus
    manuscripts: list[Manuscript] = Field(default_factory=list)
    disclosure: list[ModelProviderDisclosure] = Field(default_factory=list)
    license_audit: list[LicenseAuditEntry] = Field(default_factory=list)
    reproducibility: ReproducibilityPackage
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_bundle(self) -> "PublicationBundle":
        if self.status == "ready":
            required = {"system_paper", "benchmark_paper", "case_study"}
            present = {item.kind for item in self.manuscripts if item.status == "ready"}
            if required - present:
                raise ValueError(f"Ready bundle missing manuscripts: {sorted(required - present)}")
            if not self.disclosure:
                raise ValueError("Ready bundle requires model/provider disclosure")
            if not self.license_audit or any(item.status != "pass" for item in self.license_audit):
                raise ValueError("Ready bundle requires all licensing entries to pass")
        return self
