"""Adversarial Phase 5 verification of candidate research gaps."""

from __future__ import annotations

import hashlib
import json
import re
from collections import OrderedDict
from dataclasses import dataclass
from sqlite3 import Row
from typing import Iterable

from agentic_research.literature.service import LiteratureService
from agentic_research.retrieval.contracts import SearchQuery
from agentic_research.schemas import Paper
from agentic_research.schemas.gap import GapCandidate, GapStatus
from agentic_research.schemas.phase3 import RetrievalFilters
from agentic_research.schemas.phase5 import (
    Counterevidence,
    GapVerificationResult,
    NoveltyVerificationConfig,
    NoveltyVerificationReport,
    PriorWorkMatch,
    SearchProbe,
)
from agentic_research.world_model.store import ScientificWorldModel


_ALIAS_GROUPS = {
    "rag": "retrieval augmented generation",
    "retrieval augmented generation": "rag",
    "llm": "large language model",
    "large language model": "llm",
    "vlm": "vision language model",
    "vision language model": "vlm",
    "mlm": "masked language model",
    "masked language model": "mlm",
}

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it",
    "of", "on", "or", "that", "the", "their", "this", "to", "with", "we", "our", "using",
    "used", "use", "show", "shows", "result", "results", "method", "approach", "model", "paper",
}

_SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2}


@dataclass(frozen=True)
class _SearchRecord:
    paper_id: str
    paper_title: str
    source: str
    query: str
    paper: Paper


def _normalize(text: str) -> str:
    tokens = re.findall(r"\w+", text.casefold(), flags=re.UNICODE)
    return " ".join(token for token in tokens if token not in _STOPWORDS and len(token) > 1)


def _token_set(text: str) -> set[str]:
    return set(_normalize(text).split())


def _jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    a, b = set(left), set(right)
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha1("||".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}:{digest}"


def _field_overlap(candidate_values: list[str], paper_values: list[str]) -> float:
    candidate_tokens = {_normalize(value) for value in candidate_values if value}
    paper_tokens = {_normalize(value) for value in paper_values if value}
    if not candidate_tokens:
        return 0.0
    return max(
        (_jaccard(_token_set(value), _token_set(other)) for value in candidate_tokens for other in paper_tokens),
        default=0.0,
    )


def _paper_text(paper: Paper) -> str:
    return " ".join(
        (
            paper.title,
            paper.abstract or "",
            " ".join(paper.methods),
            " ".join(paper.tasks),
            " ".join(paper.datasets),
            " ".join(paper.limitations),
        )
    )


def _exact_combination(candidate: GapCandidate, paper: Paper) -> bool:
    candidate_method = _normalize(candidate.method or "")
    candidate_dataset = _normalize(candidate.dataset or "")
    candidate_task = _normalize(candidate.task or "")
    methods = {_normalize(value) for value in paper.methods}
    datasets = {_normalize(value) for value in paper.datasets}
    tasks = {_normalize(value) for value in paper.tasks}

    method_ok = bool(candidate_method) and candidate_method in methods
    dataset_ok = bool(candidate_dataset) and candidate_dataset in datasets
    task_ok = not candidate_task or candidate_task in tasks
    return method_ok and dataset_ok and task_ok


def _candidate_query_terms(candidate: GapCandidate) -> list[str]:
    values = [candidate.method or "", candidate.dataset or "", candidate.task or ""]
    return [value.strip() for value in values if value.strip()]


def expand_queries(candidate: GapCandidate, max_queries: int) -> list[tuple[str, str]]:
    """Create deterministic challenge probes without claiming synonym completeness."""
    terms = _candidate_query_terms(candidate)
    probes: OrderedDict[str, str] = OrderedDict()
    if candidate.statement:
        probes[candidate.statement.strip()] = "Original candidate statement"
        normalized = _normalize(candidate.statement)
        if normalized:
            probes[normalized] = "Normalized statement variant"
    if terms:
        probes[" ".join(f'"{term}"' for term in terms)] = "Exact entity combination"
        probes[" ".join(terms)] = "Unquoted entity combination"
    if candidate.method and candidate.dataset:
        probes[f'"{candidate.method}" "{candidate.dataset}"'] = "Method/dataset challenge"
    if candidate.method and candidate.task:
        probes[f'"{candidate.method}" "{candidate.task}"'] = "Method/task challenge"
    if candidate.dataset and candidate.task:
        probes[f'"{candidate.dataset}" "{candidate.task}"'] = "Dataset/task challenge"

    for term in terms:
        alias = _ALIAS_GROUPS.get(_normalize(term))
        if alias:
            for query in list(probes.keys()):
                expanded = re.sub(re.escape(term), alias, query, flags=re.IGNORECASE)
                if expanded != query:
                    probes[expanded] = f"Terminology expansion: {term} → {alias}"

    return [(query, rationale) for query, rationale in probes.items() if query.strip()][:max_queries]


class NoveltyVerifier:
    """Challenge Phase 4 candidates against local and external literature."""

    def __init__(
        self,
        world: ScientificWorldModel | None = None,
        literature_service: LiteratureService | None = None,
    ) -> None:
        self.world = world
        self.literature_service = literature_service

    def verify(self, candidate: GapCandidate, config: NoveltyVerificationConfig | None = None) -> GapVerificationResult:
        cfg = config or NoveltyVerificationConfig()
        if candidate.status != GapStatus.CANDIDATE:
            raise ValueError("Phase 5 accepts only Phase 4 candidates")

        probes = expand_queries(candidate, cfg.max_queries_per_gap)
        query_probes = [
            SearchProbe(
                probe_id=_stable_id("probe", candidate.gap_id, query),
                query=query,
                rationale=rationale,
                source="planned",
            )
            for query, rationale in probes
        ]
        records: list[_SearchRecord] = []
        limitations: list[str] = []
        searched_sources: set[str] = set()
        successful_probes = 0

        for (query, _), probe in zip(probes, query_probes, strict=True):
            probe_succeeded = False
            if cfg.include_local and self.world is not None:
                try:
                    rows = self.world.lexical_search(
                        query,
                        limit=cfg.local_results_per_query,
                        filters=RetrievalFilters(temporal_cutoff=cfg.temporal_cutoff).model_dump(),
                    )
                    probe_succeeded = True
                    paper_ids = sorted({str(row["paper_id"]) for row in rows})
                    if paper_ids:
                        placeholders = ",".join("?" for _ in paper_ids)
                        db_rows = self.world.connection.execute(
                            f"SELECT paper_id,title,year,source,doi,arxiv_id,metadata_json FROM papers WHERE paper_id IN ({placeholders})",
                            paper_ids,
                        ).fetchall()
                        for row in db_rows:
                            records.append(
                                _SearchRecord(
                                    row["paper_id"], row["title"], str(row["source"] or "local"), query, self._paper_from_row(row)
                                )
                            )
                        searched_sources.add("local-world-model")
                except Exception as exc:
                    limitations.append(f"Local search failed for probe {probe.probe_id}: {type(exc).__name__}")

            if cfg.include_external and self.literature_service is not None:
                try:
                    hits = self.literature_service.search(
                        SearchQuery(text=query, limit=cfg.external_results_per_query, temporal_cutoff=cfg.temporal_cutoff)
                    )
                    probe_succeeded = True
                    for hit in hits:
                        records.append(_SearchRecord(hit.paper.paper_id, hit.paper.title, hit.source, query, hit.paper))
                        searched_sources.add(hit.source)
                except Exception as exc:
                    limitations.append(f"External search failed for probe {probe.probe_id}: {type(exc).__name__}")

            if probe_succeeded:
                successful_probes += 1

        unique: OrderedDict[str, _SearchRecord] = OrderedDict()
        for record in records:
            unique.setdefault(record.paper_id, record)

        matches: list[PriorWorkMatch] = []
        counterevidence: list[Counterevidence] = []
        for record in unique.values():
            paper = record.paper
            if cfg.temporal_cutoff is not None and paper.year is not None and paper.year > cfg.temporal_cutoff:
                continue
            method_overlap = _field_overlap([candidate.method or ""], paper.methods)
            dataset_overlap = _field_overlap([candidate.dataset or ""], paper.datasets)
            task_overlap = _field_overlap([candidate.task or ""], paper.tasks)
            title_overlap = _jaccard(_token_set(candidate.statement), _token_set(paper.title))
            semantic_overlap = _jaccard(_token_set(candidate.statement), _token_set(_paper_text(paper)))
            exact = _exact_combination(candidate, paper)
            similarity = max(
                semantic_overlap * 0.40 + method_overlap * 0.20 + dataset_overlap * 0.20 + task_overlap * 0.15 + title_overlap * 0.05,
                max(method_overlap, dataset_overlap, task_overlap) * 0.65 + semantic_overlap * 0.35,
            )
            if exact:
                challenge_type = "direct"
                severity = "high"
            elif similarity >= cfg.near_match_similarity:
                challenge_type = "near"
                severity = "medium"
            elif similarity >= 0.45:
                challenge_type = "contextual"
                severity = "low"
            else:
                continue

            rationale = (
                "Directly reproduces the candidate combination." if exact else
                "Closely overlaps the candidate research configuration." if challenge_type == "near" else
                "Provides contextual evidence relevant to the candidate gap."
            )
            matches.append(
                PriorWorkMatch(
                    match_id=_stable_id("match", candidate.gap_id, record.paper_id),
                    paper=paper,
                    source=record.source,
                    query=record.query,
                    similarity=round(similarity, 6),
                    method_overlap=round(method_overlap, 6),
                    dataset_overlap=round(dataset_overlap, 6),
                    task_overlap=round(task_overlap, 6),
                    title_overlap=round(title_overlap, 6),
                    exact_combination=exact,
                    challenge_type=challenge_type,
                    rationale=rationale,
                )
            )
            if challenge_type in {"direct", "near"}:
                counterevidence.append(
                    Counterevidence(
                        counterevidence_id=_stable_id("counter", candidate.gap_id, record.paper_id),
                        paper_id=record.paper_id,
                        source=record.source,
                        query=record.query,
                        claim=paper.title,
                        severity=severity,
                        supports_gap=False,
                        rationale=rationale,
                    )
                )

        matches.sort(key=lambda item: (-item.similarity, item.paper.paper_id))
        counterevidence.sort(key=lambda item: (-_SEVERITY_ORDER[item.severity], item.paper_id))

        if successful_probes >= cfg.min_broad_searches and len(searched_sources) >= 2:
            coverage = "broad"
        elif successful_probes >= cfg.min_broad_searches or len(searched_sources) >= 2:
            coverage = "moderate"
        elif successful_probes > 0:
            coverage = "limited"
        else:
            coverage = "none"

        direct = [match for match in matches if match.exact_combination and match.similarity >= cfg.min_direct_similarity]
        near = [match for match in matches if match.challenge_type == "near"]
        if direct:
            verdict = "disproved"
            confidence = min(0.99, max(match.similarity for match in direct))
            resulting_status = GapStatus.DISPROVED if cfg.allow_status_transition else GapStatus.CANDIDATE
            rationale = "At least one sufficiently similar prior work directly matches the candidate combination."
        elif near:
            verdict = "weakened"
            confidence = min(0.90, max(match.similarity for match in near))
            resulting_status = GapStatus.WEAKENED if cfg.allow_status_transition else GapStatus.CANDIDATE
            rationale = "No direct match exceeded the direct threshold, but close prior work materially weakens the candidate gap."
        elif coverage in {"broad", "moderate"}:
            verdict = "supported"
            confidence = 0.55 if coverage == "moderate" else 0.65
            resulting_status = GapStatus.SURVIVED if cfg.allow_status_transition else GapStatus.CANDIDATE
            rationale = "The candidate survived the configured adversarial search budget without a direct or near prior-work match."
        else:
            verdict = "inconclusive"
            confidence = 0.25
            resulting_status = GapStatus.UNCERTAIN if cfg.allow_status_transition else GapStatus.CANDIDATE
            rationale = "Search coverage was insufficient to support or reject the candidate gap."

        if not records:
            limitations.append("No search results were retrieved; this is not evidence of novelty.")
        if "local-world-model" not in searched_sources and cfg.include_local:
            limitations.append("The local indexed corpus was not searched or returned no usable results.")
        if cfg.include_external and not any(source != "local-world-model" for source in searched_sources):
            limitations.append("No external literature provider returned usable results.")
        if coverage == "broad":
            limitations.append("Broad means broad within the configured providers and query budget, not exhaustive global coverage.")

        verified_candidate = candidate.model_copy(
            update={
                "closest_prior_work_ids": [match.paper.paper_id for match in matches[:10]],
                "counterevidence_ids": [item.counterevidence_id for item in counterevidence],
                "confidence": confidence,
                "status": resulting_status,
            }
        )

        return GapVerificationResult(
            verification_id=_stable_id("verification", candidate.gap_id, json.dumps(cfg.model_dump(mode="json"), sort_keys=True)),
            gap_id=candidate.gap_id,
            original_status=candidate.status,
            resulting_status=resulting_status,
            verdict=verdict,
            coverage=coverage,
            confidence=confidence,
            query_probes=query_probes,
            prior_work=matches[:25],
            counterevidence=counterevidence[:25],
            nearest_prior_work_ids=[match.paper.paper_id for match in matches[:10]],
            searched_sources=sorted(searched_sources),
            limitations=sorted(set(limitations)),
            rationale=rationale,
            verified_candidate=verified_candidate,
        )

    @staticmethod
    def _paper_from_row(row: Row) -> Paper:
        metadata = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
        return Paper(
            paper_id=row["paper_id"],
            title=row["title"],
            year=row["year"],
            doi=row["doi"],
            arxiv_id=row["arxiv_id"],
            metadata=metadata,
        )

    def verify_batch(self, candidates: list[GapCandidate], config: NoveltyVerificationConfig | None = None) -> NoveltyVerificationReport:
        cfg = config or NoveltyVerificationConfig()
        results = [self.verify(candidate, cfg) for candidate in candidates]
        run_id = _stable_id(
            "novelty-run",
            json.dumps(cfg.model_dump(mode="json"), sort_keys=True),
            *sorted(candidate.gap_id for candidate in candidates),
        )
        return NoveltyVerificationReport(
            run_id=run_id,
            temporal_cutoff=cfg.temporal_cutoff,
            input_candidate_count=len(candidates),
            results=results,
        )
