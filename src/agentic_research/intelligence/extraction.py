"""Deterministic structured field and claim extraction.

Phase 2 deliberately uses explainable heuristics. LLM extraction can be added
later, but this layer must remain auditable and testable without a model.
"""

from __future__ import annotations

import hashlib
import re
from collections import OrderedDict

from agentic_research.schemas import Paper
from agentic_research.schemas.paper_intelligence import (
    ClaimEvidenceLink,
    ExtractedClaim,
    Section,
    TextChunk,
)

_FIELD_TERMS: dict[str, tuple[str, ...]] = {
    "methods": ("method", "methods", "approach", "architecture", "algorithm", "model"),
    "datasets": ("dataset", "datasets", "corpus", "benchmark", "benchmarks"),
    "metrics": ("metric", "metrics", "accuracy", "precision", "recall", "f1", "auc", "bleu", "rouge"),
    "baselines": ("baseline", "baselines", "compared with", "compared to", "state-of-the-art"),
    "limitations": ("limitation", "limitations", "limited", "fails", "failure", "constraint"),
    "assumptions": ("assume", "assumption", "we suppose", "under the assumption"),
    "future_work": ("future work", "future research", "we leave", "will investigate", "remain to be studied"),
}
_RESULT_WORDS = re.compile(
    r"\b(improv(?:e|es|ed|ing)|outperform(?:s|ed)?|achiev(?:e|es|ed)|increase[ds]?|decrease[ds]?|reduce[sd]?|yield(?:s|ed)?|obtain(?:s|ed)?)\b",
    re.I,
)
_LIMITATION_WORDS = re.compile(r"\b(limit(?:ation|ations)?|fail(?:s|ed|ure)?|cannot|unable|drawback|constraint)\b", re.I)
_METHOD_WORDS = re.compile(r"\b(we propose|we introduce|we present|our method|our approach|we develop)\b", re.I)


def extract_fields(chunks: list[TextChunk], sections: list[Section]) -> dict[str, list[str]]:
    """Extract auditable candidate field strings from section-aware chunks."""
    fields: dict[str, OrderedDict[str, None]] = {
        name: OrderedDict()
        for name in _FIELD_TERMS
    }
    normalized_section = {section.section_id: section.normalized_title for section in sections}
    for chunk in chunks:
        section_name = normalized_section.get(chunk.section_id, "")
        searchable = f"{section_name} {chunk.section_title or ''}".lower()
        for field, terms in _FIELD_TERMS.items():
            if any(term in searchable for term in terms):
                for sentence in _sentences(chunk.text):
                    text = sentence.strip()
                    if text:
                        fields[field].setdefault(text, None)
    return {key: list(values.keys())[:50] for key, values in fields.items()}


def merge_extracted_fields(paper: Paper, fields: dict[str, list[str]]) -> Paper:
    """Return a copy of the Paper with deterministic extracted candidate fields."""
    updated = paper.model_copy(deep=True)
    for field in _FIELD_TERMS:
        current = list(getattr(updated, field))
        setattr(updated, field, list(dict.fromkeys(current + fields.get(field, []))))
    return updated


def extract_claims(
    paper_id: str,
    chunks: list[TextChunk],
) -> tuple[list[ExtractedClaim], list[ClaimEvidenceLink]]:
    claims: list[ExtractedClaim] = []
    links: list[ClaimEvidenceLink] = []
    for chunk in chunks:
        for sentence in _sentences(chunk.text):
            claim_type, raw_confidence = _classify_claim(sentence, chunk.section_title or "")
            if claim_type is None:
                continue
            claim_hash = hashlib.sha1(f"{paper_id}|{chunk.chunk_id}|{sentence}".encode("utf-8")).hexdigest()[:16]
            claim_id = f"claim-{claim_hash}"
            claims.append(
                ExtractedClaim(
                    claim_id=claim_id,
                    paper_id=paper_id,
                    text=sentence,
                    section_id=chunk.section_id,
                    chunk_id=chunk.chunk_id,
                    page=chunk.page_start,
                    claim_type=claim_type,
                    raw_confidence=raw_confidence,
                )
            )
            link_hash = hashlib.sha1(f"{claim_id}|{chunk.chunk_id}".encode("utf-8")).hexdigest()[:16]
            relation = "supports" if claim_type == "result" else "contextualizes"
            links.append(
                ClaimEvidenceLink(
                    link_id=f"link-{link_hash}",
                    claim_id=claim_id,
                    evidence_chunk_id=chunk.chunk_id,
                    relation=relation,
                    confidence=min(0.96, raw_confidence + 0.03),
                )
            )
    return claims, links


def _classify_claim(sentence: str, section_title: str) -> tuple[str | None, float]:
    section = section_title.lower()
    if _LIMITATION_WORDS.search(sentence) or "limitation" in section:
        return "limitation", 0.86 if _LIMITATION_WORDS.search(sentence) else 0.72
    if _METHOD_WORDS.search(sentence) or any(word in section for word in ("method", "approach", "architecture")):
        return "method", 0.84 if _METHOD_WORDS.search(sentence) else 0.66
    if _RESULT_WORDS.search(sentence) or any(word in section for word in ("result", "experiment", "evaluation")):
        return "result", 0.84 if _RESULT_WORDS.search(sentence) else 0.62
    if any(word in section for word in ("dataset", "data", "benchmark")):
        return "dataset", 0.60
    if any(word in section for word in ("evaluation", "metric")):
        return "evaluation", 0.60
    return None, 0.0


def _sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(])", normalized) if item.strip()]
