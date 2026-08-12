"""Deterministic structured field and claim extraction."""

from __future__ import annotations

import hashlib
import re
from collections import OrderedDict

from agentic_research.schemas import Evidence, Paper
from agentic_research.schemas.paper_intelligence import ClaimEvidenceLink, ExtractedClaim, Section, TextChunk

_FIELD_TERMS: dict[str, tuple[str, ...]] = {
    "methods": ("method", "methods", "approach", "architecture", "algorithm", "model"),
    "datasets": ("dataset", "datasets", "corpus", "benchmark", "benchmarks"),
    "metrics": ("metric", "metrics", "accuracy", "precision", "recall", "f1", "auc", "bleu", "rouge"),
    "baselines": ("baseline", "baselines", "compared with", "compared to", "state-of-the-art"),
    "limitations": ("limitation", "limitations", "limited", "fails", "failure", "constraint"),
    "assumptions": ("assume", "assumption", "we suppose", "under the assumption"),
    "future_work": ("future work", "future research", "we leave", "will investigate", "remain to be studied"),
}
_ENTITY_FIELDS = {"methods", "datasets", "metrics", "baselines"}
_RESULT_WORDS = re.compile(r"\b(improv(?:e|es|ed|ing)|outperform(?:s|ed)?|achiev(?:e|es|ed)|increase[ds]?|decrease[ds]?|reduce[sd]?|yield(?:s|ed)?|obtain(?:s|ed)?)\b", re.I)
_LIMITATION_WORDS = re.compile(r"\b(limit(?:ation|ations)?|fail(?:s|ed|ure)?|cannot|unable|drawback|constraint)\b", re.I)
_METHOD_WORDS = re.compile(r"\b(we propose|we introduce|we present|our method|our approach|we develop)\b", re.I)


def extract_fields(chunks: list[TextChunk], sections: list[Section]) -> dict[str, list[str]]:
    """Extract candidate entities and narrative field values with auditable heuristics."""
    fields: dict[str, OrderedDict[str, None]] = {name: OrderedDict() for name in _FIELD_TERMS}
    normalized_section = {section.section_id: section.normalized_title for section in sections}
    for chunk in chunks:
        section_name = normalized_section.get(chunk.section_id, "")
        searchable = f"{section_name} {chunk.section_title or ''}".lower()
        for field, terms in _FIELD_TERMS.items():
            if not any(term in searchable for term in terms):
                continue
            for sentence in _sentences(chunk.text):
                for value in _candidate_values(field, sentence):
                    if value:
                        fields[field].setdefault(value, None)
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
) -> tuple[list[ExtractedClaim], list[Evidence], list[ClaimEvidenceLink]]:
    claims: list[ExtractedClaim] = []
    evidence: list[Evidence] = []
    links: list[ClaimEvidenceLink] = []
    for chunk in chunks:
        for sentence in _sentences(chunk.text):
            claim_type, raw_confidence = _classify_claim(sentence, chunk.section_title or "")
            if claim_type is None:
                continue
            claim_hash = hashlib.sha1(f"{paper_id}|{chunk.chunk_id}|{sentence}".encode("utf-8")).hexdigest()[:16]
            claim_id = f"claim-{claim_hash}"
            evidence_id = f"evidence-{claim_hash}"
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
            evidence.append(
                Evidence(
                    evidence_id=evidence_id,
                    paper_id=paper_id,
                    claim=sentence,
                    section=chunk.section_title,
                    page=chunk.page_start,
                    quote=sentence,
                    source_locator=chunk.chunk_id,
                    confidence=raw_confidence,
                )
            )
            relation = "supports" if claim_type == "result" else "contextualizes"
            links.append(
                ClaimEvidenceLink(
                    link_id=f"link-{claim_hash}",
                    claim_id=claim_id,
                    evidence_id=evidence_id,
                    relation=relation,
                    confidence=min(0.96, raw_confidence + 0.03),
                )
            )
    return claims, evidence, links


def _candidate_values(field: str, sentence: str) -> list[str]:
    if field not in _ENTITY_FIELDS:
        return [sentence.strip()]
    if field == "metrics":
        known = re.findall(r"\b(?:accuracy|precision|recall|f1(?:-score)?|auc|bleu|rouge(?:-\w+)?)\b", sentence, flags=re.I)
        return [item.lower() for item in dict.fromkeys(known)]
    if field == "baselines":
        match = re.search(r"(?:compared (?:with|to)|baseline(?:s)?(?: include)?)\s+([^.;]+)", sentence, flags=re.I)
        return _clean_entity_list(match.group(1) if match else "")
    if field == "datasets":
        candidates = re.findall(r"(?:dataset|corpus|benchmark)\s*(?:called|named|:)?\s*([A-Z][A-Za-z0-9._-]*(?:\s+[A-Z][A-Za-z0-9._-]*){0,5})", sentence)
        return _clean_entity_list(", ".join(candidates))
    match = re.search(r"(?:we propose|we introduce|we present|our (?:method|approach)|we develop|using)\s+([^.;]+)", sentence, flags=re.I)
    return _clean_entity_list(match.group(1) if match else "")


def _clean_entity_list(value: str) -> list[str]:
    output: list[str] = []
    for item in re.split(r"\s*(?:,|;| and )\s*", value):
        cleaned = re.sub(r"\s+", " ", item).strip(" :.-")
        if 2 <= len(cleaned) <= 120 and not cleaned.lower().startswith(("the ", "a ", "an ")):
            output.append(cleaned)
    return list(dict.fromkeys(output))


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
