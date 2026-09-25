"""PEFT-30 corpus manifest schema and deterministic freeze tooling.

Design rules:
- Unknown fields stay unknown (Optional, never fabricated).
- Supports pdf / html / metadata-only explicitly.
- Frozen snapshots are immutable: freeze refuses to overwrite a
  different frozen manifest with the same path.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

BENCHMARK_ID = "sci-bench-peft30-v1"
TEMPORAL_CUTOFF = "2022-12-31"
CUTOFF_YEAR = 2022
DOMAIN = "parameter-efficient-fine-tuning"

FulltextStatus = Literal["pdf", "html", "metadata-only"]
FreezeStatus = Literal["draft", "frozen"]


def _canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def sha256_canonical(obj: object) -> str:
    return hashlib.sha256(_canonical(obj)).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class PaperRecord(BaseModel):
    """One corpus paper. Unknown metadata stays None, never invented."""

    model_config = ConfigDict(extra="forbid")

    paper_id: str = Field(min_length=1)
    arxiv_id: str | None = None
    doi: str | None = None
    title: str = Field(min_length=1)
    year: int | None = Field(default=None, ge=1900, le=2200)
    source: str = Field(min_length=1)
    retrieval_date: str | None = None
    fulltext_status: FulltextStatus = "metadata-only"
    local_path: str | None = None
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    license: str | None = None

    @model_validator(mode="after")
    def validate_local_artifact(self) -> PaperRecord:
        if self.fulltext_status in ("pdf", "html") and self.local_path is None:
            raise ValueError("pdf/html records require local_path")
        return self


class CorpusManifest(BaseModel):
    """Frozen-or-draft manifest for sci-bench-peft30-v1."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(default=BENCHMARK_ID)
    version: str = Field(default="v1")
    domain: str = Field(default=DOMAIN)
    temporal_cutoff: str = Field(default=TEMPORAL_CUTOFF)
    cutoff_year: int = Field(default=CUTOFF_YEAR)
    collection_date_utc: str = Field(min_length=1)
    status: FreezeStatus = "draft"
    papers: list[PaperRecord] = Field(default_factory=list)
    collection_method: str = Field(min_length=1)
    sources: list[str] = Field(default_factory=list)
    corpus_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_ids_unique(self) -> CorpusManifest:
        ids = [p.paper_id for p in self.papers]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate paper_id values are not allowed")
        return self


def paper_identity(record: PaperRecord) -> str:
    """Deterministic per-paper identity (metadata only, no file bytes)."""
    payload = {
        "paper_id": record.paper_id,
        "arxiv_id": record.arxiv_id,
        "doi": record.doi,
        "title": record.title,
        "year": record.year,
        "source": record.source,
        "fulltext_status": record.fulltext_status,
        "sha256": record.sha256,
    }
    return sha256_canonical(payload)


def compute_corpus_sha256(papers: list[PaperRecord]) -> str:
    identities = sorted(paper_identity(p) for p in papers)
    return sha256_canonical({"papers": identities})


def compute_manifest_sha256(manifest: CorpusManifest) -> str:
    payload = manifest.model_dump(exclude={"manifest_sha256"})
    return sha256_canonical(payload)


def build_draft_manifest(
    papers: list[PaperRecord],
    *,
    collection_method: str,
    sources: list[str],
    collection_date_utc: str | None = None,
) -> CorpusManifest:
    corpus_hash = compute_corpus_sha256(papers)
    draft = CorpusManifest(
        collection_date_utc=collection_date_utc or utc_now_iso(),
        status="draft",
        papers=papers,
        collection_method=collection_method,
        sources=sources,
        corpus_sha256=corpus_hash,
        manifest_sha256="0" * 64,
    )
    draft.manifest_sha256 = compute_manifest_sha256(draft)
    return draft


def validate_manifest(manifest: CorpusManifest, *, corpus_root: Path | None = None) -> list[str]:
    """Return a list of problems (empty means valid).

    Checks hash consistency and, when corpus_root is given, that every
    pdf/html local_path exists and its bytes match sha256 when provided.
    """
    problems: list[str] = []
    if manifest.benchmark_id != BENCHMARK_ID:
        problems.append(f"unexpected benchmark_id {manifest.benchmark_id!r}")
    if manifest.temporal_cutoff != TEMPORAL_CUTOFF:
        problems.append("temporal_cutoff must be 2022-12-31")
    if manifest.cutoff_year != CUTOFF_YEAR:
        problems.append("cutoff_year must be 2022")
    if compute_corpus_sha256(manifest.papers) != manifest.corpus_sha256:
        problems.append("corpus_sha256 mismatch")
    if compute_manifest_sha256(manifest) != manifest.manifest_sha256:
        problems.append("manifest_sha256 mismatch")
    if corpus_root is not None:
        for paper in manifest.papers:
            if paper.fulltext_status in ("pdf", "html"):
                if paper.local_path is None:
                    problems.append(f"{paper.paper_id}: missing local_path")
                    continue
                path = corpus_root / paper.local_path
                if not path.is_file():
                    problems.append(f"{paper.paper_id}: missing artifact {paper.local_path}")
                    continue
                if paper.sha256 is not None:
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                    if digest != paper.sha256:
                        problems.append(f"{paper.paper_id}: sha256 mismatch")
    return problems


def temporal_split(manifest: CorpusManifest) -> dict[str, list[str]]:
    """Split paper_ids into pre-cutoff / post-cutoff-probe / unknown-year."""
    pre: list[str] = []
    post: list[str] = []
    unknown: list[str] = []
    for paper in manifest.papers:
        if paper.year is None:
            unknown.append(paper.paper_id)
        elif paper.year <= CUTOFF_YEAR:
            pre.append(paper.paper_id)
        else:
            post.append(paper.paper_id)
    return {
        "discovery": sorted(pre),
        "post_cutoff_probes": sorted(post),
        "unknown_year": sorted(unknown),
    }


def freeze_manifest(
    manifest: CorpusManifest,
    output_path: Path,
    *,
    corpus_root: Path | None = None,
) -> Path:
    """Validate, mark frozen, and write. Refuses to mutate an existing snapshot."""
    problems = validate_manifest(manifest, corpus_root=corpus_root)
    if problems:
        raise ValueError("Refusing to freeze invalid manifest: " + "; ".join(problems))
    frozen = manifest.model_copy(update={"status": "frozen"})
    frozen.manifest_sha256 = compute_manifest_sha256(frozen)
    payload = frozen.model_dump()
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output_path.exists():
        existing = output_path.read_text(encoding="utf-8")
        if existing == text:
            return output_path
        raise ValueError(
            f"Refusing to overwrite existing frozen snapshot at {output_path} "
            "(delete explicitly only via a new benchmark version)"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    (output_path.parent / (output_path.stem + ".sha256")).write_text(
        hashlib.sha256(text.encode("utf-8")).hexdigest() + "\n", encoding="utf-8"
    )
    return output_path
