"""Deterministic reference and citation extraction for scientific PDFs."""

from __future__ import annotations

import hashlib
import re

from agentic_research.literature.identity import normalize_arxiv_id, normalize_doi
from agentic_research.schemas import Paper
from agentic_research.schemas.paper_intelligence import CitationEdge, CitationReference, TextChunk

_NUMERIC_REF = re.compile(r"\[(\d{1,4})\]")
_NUMERIC_RANGE = re.compile(r"\[(\d{1,4})\s*[-–]\s*(\d{1,4})\]")
_DOI = re.compile(r"\b10\.\d{4,9}/[-._;()/:a-z0-9]+", re.I)
_ARXIV = re.compile(r"\b(?:arxiv:)?(\d{4}\.\d{4,5})(?:v\d+)?\b", re.I)
_YEAR = re.compile(r"\b(18\d{2}|19\d{2}|20\d{2}|21\d{2})\b")


def split_reference_entries(text: str) -> list[tuple[int | None, str]]:
    """Split a bibliography into conservative reference entries."""
    clean_lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    clean_lines = [line for line in clean_lines if line]
    entries: list[tuple[int | None, str]] = []
    current_number: int | None = None
    current: list[str] = []
    start_pattern = re.compile(r"^\[?(\d{1,4})\]?\s*[.)]?\s+(.+)$")

    for line in clean_lines:
        match = start_pattern.match(line)
        if match:
            if current:
                entries.append((current_number, " ".join(current)))
            current_number = int(match.group(1))
            current = [match.group(2)]
        elif current:
            current.append(line)
        else:
            current = [line]
    if current:
        entries.append((current_number, " ".join(current)))
    return entries


def extract_references(paper: Paper, references_text: str) -> list[CitationReference]:
    references: list[CitationReference] = []
    for index, (order, raw_text) in enumerate(split_reference_entries(references_text), start=1):
        doi_match = _DOI.search(raw_text)
        arxiv_match = _ARXIV.search(raw_text)
        year_match = _YEAR.search(raw_text)
        ref_id = hashlib.sha1(f"{paper.paper_id}|ref|{order or index}|{raw_text}".encode("utf-8")).hexdigest()[:16]
        references.append(
            CitationReference(
                reference_id=f"ref-{ref_id}",
                paper_id=paper.paper_id,
                order=order or index,
                raw_text=raw_text,
                title=_guess_title(raw_text),
                year=int(year_match.group(1)) if year_match else None,
                doi=normalize_doi(doi_match.group(0)) if doi_match else None,
                arxiv_id=normalize_arxiv_id(arxiv_match.group(1)) if arxiv_match else None,
                extraction_confidence=_reference_confidence(raw_text, bool(doi_match or arxiv_match), bool(year_match)),
            )
        )
    return references


def extract_citation_edges(
    paper: Paper,
    chunks: list[TextChunk],
    references: list[CitationReference],
) -> list[CitationEdge]:
    by_number = {ref.order: ref for ref in references if ref.order is not None}
    edges: dict[str, CitationEdge] = {}
    for chunk in chunks:
        for number, marker in _citation_numbers(chunk.text):
            ref = by_number.get(number)
            if ref is None:
                continue
            edge_id = hashlib.sha1(f"{paper.paper_id}|{ref.reference_id}|{chunk.chunk_id}".encode("utf-8")).hexdigest()[:16]
            edges[edge_id] = CitationEdge(
                edge_id=f"edge-{edge_id}",
                citing_paper_id=paper.paper_id,
                cited_reference_id=ref.reference_id,
                cited_paper_id=_resolved_cited_paper_id(ref),
                citation_context_chunk_id=chunk.chunk_id,
                marker=marker,
                confidence=0.93,
            )
    return list(edges.values())


def _citation_numbers(text: str) -> list[tuple[int, str]]:
    numbers: list[tuple[int, str]] = []
    ranged_spans: list[tuple[int, int]] = []
    for match in _NUMERIC_RANGE.finditer(text):
        start, end = int(match.group(1)), int(match.group(2))
        if end >= start and end - start <= 50:
            ranged_spans.append((match.start(), match.end()))
            for number in range(start, end + 1):
                numbers.append((number, match.group(0)))
    for match in _NUMERIC_REF.finditer(text):
        if any(start <= match.start() < end for start, end in ranged_spans):
            continue
        numbers.append((int(match.group(1)), match.group(0)))
    return numbers


def _guess_title(raw: str) -> str | None:
    parts = [part.strip() for part in raw.split(".") if part.strip()]
    if len(parts) < 2:
        return None
    return max(parts[1:-1] or parts[1:], key=len)[:300]


def _reference_confidence(raw: str, has_identifier: bool, has_year: bool) -> float:
    score = 0.45
    if has_identifier:
        score += 0.30
    if has_year:
        score += 0.15
    if len(raw) >= 40:
        score += 0.08
    return min(score, 0.98)


def _resolved_cited_paper_id(reference: CitationReference) -> str | None:
    if reference.doi:
        return f"doi:{reference.doi}"
    if reference.arxiv_id:
        return f"arxiv:{reference.arxiv_id}"
    return None
