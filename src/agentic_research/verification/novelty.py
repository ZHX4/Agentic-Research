"""Adversarial Phase 5 verification of candidate research gaps."""

from __future__ import annotations

import hashlib
import json
import re
from collections import OrderedDict
from dataclasses import dataclass
from sqlite3 import Row
from typing import Iterable

from agentic_research.intelligence.pipeline import extract_paper_intelligence
from agentic_research.literature.fulltext import FullTextAcquirer, parse_full_text
from agentic_research.literature.service import LiteratureService
from agentic_research.retrieval.contracts import SearchQuery
from agentic_research.schemas import Paper
from agentic_research.schemas.gap import GapCandidate, GapStatus
from agentic_research.schemas.phase3 import RetrievalFilters
from agentic_research.schemas.phase5 import (
    Counterevidence,
    DeepEvidenceCheck,
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
    return (
        bool(candidate_method)
        and candidate_method in methods
        and bool(candidate_dataset)
        and candidate_dataset in datasets
        and (not candidate_task or candidate_task in tasks)
    )


def _candidate_query_terms(candidate: GapCandidate) -> list[str]:
    return [
        value.strip()
        for value in [candidate.method or "", candidate.dataset or "", candidate.task or ""]
        if value.strip()
    ]


def _fulltext_exact_combination(text: str, candidate: GapCandidate) -> tuple[bool, bool, bool, bool]:
    """Check whether all candidate entities occur in one local full-text context."""
    paragraphs = [chunk for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
    terms = {
        "method": _normalize(candidate.method or ""),
        "dataset": _normalize(candidate.dataset or ""),
        "task": _normalize(candidate.task or ""),
    }
    found_method = bool(terms["method"]) and any(terms["method"] in _normalize(p) for p in paragraphs)
    found_dataset = bool(terms["dataset"]) and any(terms["dataset"] in _normalize(p) for p in paragraphs)
    found_task = not terms["task"] or any(terms["task"] in _normalize(p) for p in paragraphs)
    same_context = False
    for paragraph in paragraphs:
        normalized = _normalize(paragraph)
        if (
            (not terms["method"] or terms["method"] in normalized)
            and (not terms["dataset"] or terms["dataset"] in normalized)
            and (not terms["task"] or terms["task"] in normalized)
        ):
            same_context = True
            break
    return found_method, found_dataset, found_task, same_context


def _candidate_query_terms_text(candidate: GapCandidate) -> list[str]:
    return _candidate_query_terms(candidate)


def expand_queries(candidate: GapCandidate, max_queries: int) -> list[tuple[str, str]]:
    """Create deterministic challenge probes without claiming synonym completeness."""
    terms = _candidate_query_terms_text(candidate)
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
                expanded = re.sub(rf"\b{re.escape(term)}\b", alias, query, flags=re.IGNORECASE)
                if expanded != query:
                    probes[expanded] = f"Terminology expansion: {term} → {alias}"

    return [(query, rationale) for query, rationale in probes.items() if query.strip()][:max_queries]


class NoveltyVerifier:
    """Challenge Phase 4 candidates against local and external literature."""

    def __init__(
        self,
        world: ScientificWorldModel | None = None,
        literature_service: LiteratureService | None = None,
        fulltext_acquirer: FullTextAcquirer | None = None,
    ) -> None:
        self.world = world
        self.literature_service = literature_service
        self.fulltext_acquirer = fulltext_acquirer

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
                                    row["paper_id"],
                                    row["title"],
                                    "local-world-model",
                                    query,
                                    self._paper_from_row(row),
                                )
                            )
                        searched_sources.add("local-world-model")
                except Exception as exc:
                    limitations.append(f"Local search failed for probe {probe.probe_id}: {type(exc).__name__}")

            if cfg.include_external and self.literature_service is not None:
                try:
                    hits = self.literature_service.search(
                        SearchQuery(
                            text=query,
                            limit=cfg.external_results_per_query,
                            temporal_cutoff=cfg.temporal_cutoff,
                        )
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
            if cfg.temporal_cutoff is not None and (paper.year is None or paper.year > cfg.temporal_cutoff):
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
                challenge_type, severity = "direct", "high"
            elif similarity >= cfg.near_match_similarity:
                challenge_type, severity = "near", "medium"
            elif similarity >= 0.45:
                challenge_type, severity = "contextual", "low"
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

        deep_evidence, deep_exact_ids, deep_not_found_ids = self._deep_verify_matches(candidate, matches, cfg)
        if deep_exact_ids:
            adjusted_matches = []
            for match in matches:
                if match.paper.paper_id in deep_exact_ids:
                    adjusted_matches.append(
                        match.model_copy(
                            update={
                                "exact_combination": True,
                                "challenge_type": "direct",
                                "similarity": 1.0,
                                "rationale": "Full-text evidence confirms the candidate method/dataset/task combination in the same local context.",
                            }
                        )
                    )
                else:
                    adjusted_matches.append(match)
            matches = adjusted_matches
            existing_counters = {item.paper_id for item in counterevidence}
            for paper_id in sorted(deep_exact_ids):
                if paper_id not in existing_counters:
                    counterevidence.append(
                        Counterevidence(
                            counterevidence_id=_stable_id("counter", candidate.gap_id, paper_id),
                            paper_id=paper_id,
                            source="fulltext",
                            query="deep-fulltext-check",
                            claim="Full-text evidence contains the candidate combination.",
                            severity="high",
                            supports_gap=False,
                            rationale="Full-text verification directly contradicts the candidate gap.",
                        )
                    )
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
        deep_successes = [item for item in deep_evidence if item.status in {"exact", "not_found"}]
        supported_coverage = coverage in {"broad", "moderate"}
        if direct:
            verdict, confidence, resulting_status, rationale = (
                "disproved",
                min(0.99, max(match.similarity for match in direct)),
                GapStatus.DISPROVED,
                "At least one sufficiently similar prior work directly matches the candidate combination.",
            )
        elif near:
            verdict, confidence, resulting_status, rationale = (
                "weakened",
                min(0.90, max(match.similarity for match in near)),
                GapStatus.WEAKENED,
                "No direct match was established, but close prior work materially weakens the candidate gap.",
            )
        elif supported_coverage and (not cfg.require_deep_verification_for_supported or deep_successes):
            verdict, confidence, resulting_status, rationale = (
                "supported",
                0.55 if coverage == "moderate" else 0.65,
                GapStatus.SURVIVED,
                "The candidate survived the configured adversarial search budget and the available deep checks without a direct or near prior-work match.",
            )
        else:
            verdict, confidence, resulting_status, rationale = (
                "inconclusive",
                0.25,
                GapStatus.UNCERTAIN,
                "Search or deep-evidence coverage was insufficient to support or reject the candidate gap.",
            )

        if not cfg.allow_status_transition:
            resulting_status = GapStatus.CANDIDATE
        if not records:
            limitations.append("No search results were retrieved; this is not evidence of novelty.")
        if "local-world-model" not in searched_sources and cfg.include_local:
            limitations.append("The local indexed corpus was not searched or returned no usable results.")
        if cfg.include_external and not any(source != "local-world-model" for source in searched_sources):
            limitations.append("No external literature provider returned usable results.")
        if cfg.deep_verify and self.fulltext_acquirer is None:
            limitations.append("Deep full-text verification was requested but no full-text acquirer was configured.")
        if cfg.require_deep_verification_for_supported and cfg.deep_verify and not deep_successes:
            limitations.append("A supported novelty verdict requires at least one successful deep evidence check.")
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
            deep_evidence=deep_evidence[:25],
            counterevidence=counterevidence[:25],
            nearest_prior_work_ids=[match.paper.paper_id for match in matches[:10]],
            searched_sources=sorted(searched_sources),
            limitations=sorted(set(limitations)),
            rationale=rationale,
            verified_candidate=verified_candidate,
        )

    def _deep_verify_matches(
        self,
        candidate: GapCandidate,
        matches: list[PriorWorkMatch],
        config: NoveltyVerificationConfig,
    ) -> tuple[list[DeepEvidenceCheck], set[str], set[str]]:
        if not config.deep_verify or config.max_deep_verifications == 0:
            return [], set(), set()
        if self.fulltext_acquirer is None:
            return [], set(), set()
        evidence: list[DeepEvidenceCheck] = []
        exact_ids: set[str] = set()
        not_found_ids: set[str] = set()
        eligible = [
            match
            for match in matches
            if match.similarity >= config.deep_verification_similarity_floor
            and match.source != "local-world-model"
        ][: config.max_deep_verifications]
        for match in eligible:
            check_id = _stable_id("deep", candidate.gap_id, match.paper.paper_id)
            try:
                manifest = self.fulltext_acquirer.acquire(match.paper)
                if manifest.status != "downloaded" or not manifest.local_path:
                    evidence.append(
                        DeepEvidenceCheck(
                            check_id=check_id,
                            paper_id=match.paper.paper_id,
                            source=match.source,
                            attempted=True,
                            status="unavailable" if manifest.status == "not_found" else "failed",
                            media_type=manifest.media_type,
                            rationale=manifest.error or "Full text was not available.",
                        )
                    )
                    continue
                if manifest.media_type == "application/pdf":
                    enriched, _ = extract_paper_intelligence(match.paper, __import__("pathlib").Path(manifest.local_path))
                    method_found = _normalize(candidate.method or "") in {_normalize(value) for value in enriched.methods}
                    dataset_found = _normalize(candidate.dataset or "") in {_normalize(value) for value in enriched.datasets}
                    task_found = not candidate.task or _normalize(candidate.task) in {_normalize(value) for value in enriched.tasks}
                    parsed_text = ""
                    same_context = method_found and dataset_found and task_found
                else:
                    parsed = parse_full_text(manifest)
                    parsed_text = parsed.text
                    method_found, dataset_found, task_found, same_context = _fulltext_exact_combination(parsed_text, candidate)
                if same_context:
                    exact_ids.add(match.paper.paper_id)
                    status = "exact"
                    rationale = "Full-text verification found all candidate entities in the same scientific context."
                else:
                    not_found_ids.add(match.paper.paper_id)
                    status = "not_found"
                    rationale = "Full-text was available, but the candidate combination was not jointly supported by the extracted structure/text."
                evidence.append(
                    DeepEvidenceCheck(
                        check_id=check_id,
                        paper_id=match.paper.paper_id,
                        source=match.source,
                        attempted=True,
                        status=status,
                        media_type=manifest.media_type,
                        method_found=method_found,
                        dataset_found=dataset_found,
                        task_found=task_found,
                        same_context_found=same_context,
                        local_path=manifest.local_path,
                        sha256=manifest.sha256,
                        rationale=rationale,
                    )
                )
            except Exception as exc:
                evidence.append(
                    DeepEvidenceCheck(
                        check_id=check_id,
                        paper_id=match.paper.paper_id,
                        source=match.source,
                        attempted=True,
                        status="failed",
                        media_type="unknown",
                        rationale=f"Deep full-text verification failed: {type(exc).__name__}.",
                    )
                )
        return evidence, exact_ids, not_found_ids

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
