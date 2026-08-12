"""Full-text acquisition manifests and deterministic document parsing."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import fitz  # type: ignore[import-untyped]
from bs4 import BeautifulSoup
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from agentic_research.literature.transport import HttpClient
from agentic_research.schemas import Paper


class FullTextManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    requested_url: HttpUrl
    final_url: HttpUrl | None = None
    media_type: Literal["application/pdf", "text/html", "unknown"]
    status: Literal["downloaded", "not_found", "failed"]
    local_path: str | None = None
    sha256: str | None = None
    byte_size: int = Field(default=0, ge=0)
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error: str | None = None


class ParsedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_id: str
    source_path: str
    media_type: Literal["application/pdf", "text/html", "unknown"]
    title: str | None = None
    text: str
    page_count: int | None = None


class FullTextAcquirer:
    """Acquire open full text without making acquisition a scientific claim."""

    def __init__(self, *, client: HttpClient, output_dir: Path) -> None:
        self._client = client
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def acquire(self, paper: Paper) -> FullTextManifest:
        candidates = _candidate_urls(paper)
        if not candidates:
            raise ValueError(f"No full-text candidate URL available for {paper.paper_id}")

        last_error: str | None = None
        for source, url in candidates:
            try:
                response = self._client.get(url)
                media_type = _media_type(response.headers.get("content-type", ""), response.url.path)
                if media_type == "unknown":
                    last_error = f"Unsupported content type: {response.headers.get('content-type', '')}"
                    continue
                payload = response.content
                digest = hashlib.sha256(payload).hexdigest()
                extension = ".pdf" if media_type == "application/pdf" else ".html"
                path = self._output_dir / f"{_safe_id(paper.paper_id)}-{digest[:16]}{extension}"
                path.write_bytes(payload)
                return FullTextManifest(
                    paper_id=paper.paper_id,
                    source=source,
                    requested_url=url,
                    final_url=response.url,
                    media_type=media_type,
                    status="downloaded",
                    local_path=str(path),
                    sha256=digest,
                    byte_size=len(payload),
                )
            except Exception as exc:
                last_error = str(exc)

        return FullTextManifest(
            paper_id=paper.paper_id,
            source=";".join(source for source, _ in candidates),
            requested_url=candidates[0][1],
            media_type="unknown",
            status="failed",
            error=last_error or "Unknown acquisition error",
        )


def parse_full_text(manifest: FullTextManifest) -> ParsedDocument:
    if manifest.status != "downloaded" or not manifest.local_path:
        raise ValueError("Cannot parse a manifest that was not downloaded successfully")
    path = Path(manifest.local_path)
    if not path.is_file():
        raise FileNotFoundError(path)

    if manifest.media_type == "application/pdf":
        return _parse_pdf(manifest.paper_id, path, manifest.media_type)
    if manifest.media_type == "text/html":
        return _parse_html(manifest.paper_id, path, manifest.media_type)
    raise ValueError(f"Unsupported media type: {manifest.media_type}")


def _candidate_urls(paper: Paper) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    metadata = paper.metadata
    pdf = metadata.get("open_access_pdf_url")
    if isinstance(pdf, str) and pdf:
        values.append(("open_access_pdf", pdf))
    if paper.arxiv_id:
        values.append(("arxiv_pdf", f"https://arxiv.org/pdf/{paper.arxiv_id}.pdf"))
    if paper.url is not None:
        values.append(("landing_page", str(paper.url)))
    return list(dict.fromkeys(values))


def _safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value)[:120]


def _media_type(content_type: str, path: str) -> Literal["application/pdf", "text/html", "unknown"]:
    content_type = content_type.split(";", 1)[0].strip().lower()
    if content_type == "application/pdf" or path.lower().endswith(".pdf"):
        return "application/pdf"
    if content_type in {"text/html", "application/xhtml+xml"} or re.search(r"\.html?$", path, re.I):
        return "text/html"
    return "unknown"


def _parse_pdf(paper_id: str, path: Path, media_type: Literal["application/pdf", "text/html", "unknown"]) -> ParsedDocument:
    with fitz.open(path) as document:
        text = "\n\n".join(page.get_text("text") for page in document)
        title = document.metadata.get("title") or None
        return ParsedDocument(
            paper_id=paper_id,
            source_path=str(path),
            media_type=media_type,
            title=title,
            text=text.strip(),
            page_count=document.page_count,
        )


def _parse_html(paper_id: str, path: Path, media_type: Literal["application/pdf", "text/html", "unknown"]) -> ParsedDocument:
    soup = BeautifulSoup(path.read_bytes(), "html.parser")
    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()
    title = soup.title.get_text(" ", strip=True) if soup.title else None
    text = "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())
    return ParsedDocument(
        paper_id=paper_id,
        source_path=str(path),
        media_type=media_type,
        title=title,
        text=text,
    )
