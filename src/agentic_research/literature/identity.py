"""Canonical scientific identity and deterministic deduplication."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import defaultdict
from typing import Iterable

from agentic_research.schemas import Paper

_DOI_PREFIX = re.compile(r"^(?:https?://)?(?:dx\.)?doi\.org/", re.IGNORECASE)
_ARXIV_PREFIX = re.compile(r"^(?:https?://)?(?:export\.)?arxiv\.org/(?:abs|pdf)/", re.IGNORECASE)
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    value = unicodedata.normalize("NFKC", value).strip().lower()
    value = value.removeprefix("doi:").strip()
    value = _DOI_PREFIX.sub("", value).strip()
    return value.rstrip(".") or None


def normalize_arxiv_id(value: str | None) -> str | None:
    if not value:
        return None
    value = unicodedata.normalize("NFKC", value).strip().lower()
    value = _ARXIV_PREFIX.sub("", value)
    value = value.removeprefix("arxiv:").strip()
    if value.endswith(".pdf"):
        value = value[:-4]
    # Version suffixes represent revisions of the same work for canonical identity.
    value = re.sub(r"v\d+$", "", value)
    return value or None


def normalize_title(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return " ".join(_NON_ALNUM.sub(" ", value.lower()).split())


def normalize_author(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return " ".join(_NON_ALNUM.sub(" ", value.lower()).split())


def canonical_identity(paper: Paper) -> str:
    """Return the strongest deterministic identifier available for a paper."""
    doi = normalize_doi(paper.doi)
    if doi:
        return f"doi:{doi}"

    arxiv_id = normalize_arxiv_id(paper.arxiv_id)
    if arxiv_id:
        return f"arxiv:{arxiv_id}"

    source_ids = paper.metadata.get("source_ids", {})
    if isinstance(source_ids, dict):
        for source in ("semantic_scholar", "openalex"):
            source_id = source_ids.get(source)
            if isinstance(source_id, str) and source_id.strip():
                return f"{source}:{source_id.strip().lower()}"

    authors = [normalize_author(author) for author in paper.authors[:2] if author]
    fingerprint = "|".join(
        [normalize_title(paper.title), str(paper.year or ""), *authors]
    )
    return f"fingerprint:{hashlib.sha256(fingerprint.encode('utf-8')).hexdigest()[:24]}"


def _merge_strings(left: list[str], right: list[str]) -> list[str]:
    return list(dict.fromkeys([*left, *right]))


def merge_papers(papers: Iterable[Paper]) -> Paper:
    """Merge source records deterministically, preferring populated metadata."""
    records = list(papers)
    if not records:
        raise ValueError("Cannot merge an empty paper collection")
    records.sort(key=lambda paper: (len(paper.abstract or ""), len(paper.authors), len(paper.metadata)), reverse=True)
    base = records[0].model_copy(deep=True)

    for record in records[1:]:
        if not base.abstract and record.abstract:
            base.abstract = record.abstract
        if not base.year and record.year:
            base.year = record.year
        base.authors = _merge_strings(base.authors, record.authors)
        base.methods = _merge_strings(base.methods, record.methods)
        base.tasks = _merge_strings(base.tasks, record.tasks)
        base.datasets = _merge_strings(base.datasets, record.datasets)
        base.metrics = _merge_strings(base.metrics, record.metrics)
        base.baselines = _merge_strings(base.baselines, record.baselines)
        base.limitations = _merge_strings(base.limitations, record.limitations)
        base.assumptions = _merge_strings(base.assumptions, record.assumptions)
        base.future_work = _merge_strings(base.future_work, record.future_work)
        base.evidence.extend(record.evidence)
        base.metadata = {**record.metadata, **base.metadata}
        base.paper_id = canonical_identity(base)

    # Keep evidence deterministic and unique by evidence id.
    base.evidence = list({item.evidence_id: item for item in base.evidence}.values())
    return base


def deduplicate_papers(papers: Iterable[Paper]) -> list[Paper]:
    groups: dict[str, list[Paper]] = defaultdict(list)
    for paper in papers:
        groups[canonical_identity(paper)].append(paper)

    merged = [merge_papers(group) for _, group in sorted(groups.items())]
    merged.sort(key=lambda paper: (paper.year or 0, paper.title.lower()), reverse=True)
    return merged
