"""Deterministic Phase 4 research-gap discovery over the scientific world model."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import defaultdict
from typing import Iterable

from agentic_research.schemas.gap import GapCandidate
from agentic_research.schemas.phase4 import GapDiscoveryConfig, GapDiscoveryResult, GapSignal
from agentic_research.world_model.store import ScientificWorldModel

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it",
    "of", "on", "or", "that", "the", "their", "this", "to", "with", "we", "our", "using",
    "used", "use", "show", "shows", "results", "result", "method", "approach", "model", "study",
    "paper", "performance", "significantly",
}
_POSITIVE = {
    "improve", "improves", "improved", "improving", "increase", "increases", "increased", "higher",
    "better", "outperform", "outperforms", "outperformed", "boost", "boosts", "benefit", "benefits",
    "effective", "significant", "wins", "gain", "gains",
}
_NEGATIVE = {
    "decrease", "decreases", "decreased", "lower", "lowers", "worse", "underperform", "underperforms",
    "harm", "harms", "hurt", "hurts", "degrade", "degrades", "failure", "fails", "failed",
    "ineffective", "insignificant",
}
_NEGATED_POSITIVE_PATTERNS = (
    r"\bdoes not\s+(?:significantly\s+)?improv(?:e|es|ed|ing)\b",
    r"\bdo not\s+(?:significantly\s+)?improv(?:e|es|ed|ing)\b",
    r"\bdid not\s+(?:significantly\s+)?improv(?:e|es|ed|ing)\b",
    r"\bnot\s+(?:significantly\s+)?better\b",
    r"\bno\s+improvement\b",
    r"\bwithout\s+(?:any\s+)?improvement\b",
    r"\bfails?\s+to\s+(?:significantly\s+)?improv(?:e|es|ed|ing)\b",
)
_CONDITION_KEYS = {
    "condition", "conditions", "setting", "settings", "language", "languages", "modality", "modalities",
    "resource", "resources", "resource_regime", "data_regime", "regime", "population", "environment",
    "hardware", "scale", "data_scale", "dataset_scale",
}
_DOMAIN_KEYS = {"domain", "domains", "field", "fields", "application_domain", "application_domains"}


def _normalize(text: str) -> str:
    tokens = re.findall(r"\w+", text.casefold(), flags=re.UNICODE)
    return " ".join(token for token in tokens if token not in _STOPWORDS and len(token) > 1)


def _stable_id(prefix: str, parts: Iterable[str]) -> str:
    digest = hashlib.sha1("||".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}:{digest}"


def _entity_node_id(kind: str, normalized_value: str) -> str:
    digest = hashlib.sha1(normalized_value.encode("utf-8")).hexdigest()[:20]
    return f"{kind}:{digest}"


def _mean_score(*values: float) -> float:
    if not values:
        return 0.0
    return max(0.0, min(1.0, sum(values) / len(values)))


def _iter_strings(value: object) -> Iterable[str]:
    if isinstance(value, str) and value.strip():
        yield value.strip()
    elif isinstance(value, list):
        for item in value:
            yield from _iter_strings(item)


def _metadata_values(metadata: dict[str, object], keys: set[str]) -> set[str]:
    values: set[str] = set()
    for key, value in metadata.items():
        if key.casefold() not in keys:
            continue
        for item in _iter_strings(value):
            normalized = _normalize(item)
            if normalized and len(item) <= 200:
                values.add(normalized)
    return values


def _claim_polarity(text: str) -> tuple[bool, bool]:
    """Return positive/negative result polarity with simple negation handling."""
    folded = text.casefold()
    negated_positive = any(re.search(pattern, folded) for pattern in _NEGATED_POSITIVE_PATTERNS)
    tokens = set(_normalize(text).split())
    positive = bool(tokens & _POSITIVE) and not negated_positive
    negative = bool(tokens & _NEGATIVE) or negated_positive
    return positive, negative


def _load_snapshot(world: ScientificWorldModel, cutoff: int | None) -> tuple[list[sqlite3.Row], dict[str, dict[str, set[str]]], dict[str, dict[str, set[str]]]]:
    rows = world.connection.execute("SELECT paper_id,title,year,source,metadata_json FROM papers ORDER BY paper_id").fetchall()
    papers = [row for row in rows if cutoff is None or (row["year"] is not None and row["year"] <= cutoff)]
    allowed = {row["paper_id"] for row in papers}
    by_paper: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    entity_papers: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    field_map = {"has_method": "methods", "has_dataset": "datasets", "has_task": "tasks", "has_metric": "metrics", "has_baseline": "baselines"}
    rows = world.connection.execute("""
        SELECT e.source_id, e.edge_type, n.label
        FROM edges e JOIN nodes n ON n.node_id=e.target_id
        WHERE e.edge_type IN ('has_method','has_dataset','has_task','has_metric','has_baseline')
        ORDER BY e.source_id,e.edge_type,n.node_id
    """).fetchall()
    for row in rows:
        source = row["source_id"]
        if not source.startswith("paper:"):
            continue
        paper_id = source[len("paper:"):]
        if paper_id not in allowed:
            continue
        value = _normalize(row["label"])
        if value:
            field = field_map[row["edge_type"]]
            by_paper[paper_id][field].add(value)
            entity_papers[field][value].add(paper_id)
    return papers, by_paper, entity_papers


def _load_claims(world: ScientificWorldModel, allowed: set[str]) -> list[dict[str, object]]:
    claims: list[dict[str, object]] = []
    rows = world.connection.execute("SELECT node_id,paper_id,label,payload_json FROM nodes WHERE node_type='claim' AND paper_id IS NOT NULL ORDER BY node_id").fetchall()
    for row in rows:
        if row["paper_id"] not in allowed:
            continue
        try:
            payload = json.loads(row["payload_json"])
        except json.JSONDecodeError:
            payload = {}
        claims.append({"node_id": row["node_id"], "paper_id": row["paper_id"], "label": row["label"], "claim_type": payload.get("claim_type", "")})
    return claims


def _candidate(signal: GapSignal, *, method: str | None = None, task: str | None = None, dataset: str | None = None, coverage: float | None = None) -> GapCandidate:
    return GapCandidate(
        gap_id=_stable_id("gap", [signal.signal_id]),
        gap_type=signal.gap_type,
        statement=signal.statement,
        method=method or signal.entity_values.get("method"),
        task=task or signal.entity_values.get("task"),
        dataset=dataset or signal.entity_values.get("dataset"),
        evidence_paper_ids=sorted(set(signal.paper_ids)),
        search_queries=[signal.statement],
        signal_ids=[signal.signal_id],
        support_count=signal.support_count,
        coverage_ratio=coverage,
        structural_support=signal.structural_score,
        confidence=signal.structural_score,
        status="candidate",
        rationale="Deterministic structural signal from the indexed corpus. Phase 4 does not verify novelty, search hidden literature, or perform adversarial review.",
    )


def _missing_combinations(by_paper: dict[str, dict[str, set[str]]], entity_papers: dict[str, dict[str, set[str]]], cfg: GapDiscoveryConfig) -> tuple[list[GapSignal], list[GapCandidate]]:
    methods, datasets, tasks = entity_papers["methods"], entity_papers["datasets"], entity_papers["tasks"]
    direct_md = {(m, d) for fields in by_paper.values() for m in fields.get("methods", set()) for d in fields.get("datasets", set())}
    direct_mt = {(m, t) for fields in by_paper.values() for m in fields.get("methods", set()) for t in fields.get("tasks", set())}
    method_tasks = {m: set().union(*(by_paper[p].get("tasks", set()) for p in ps)) for m, ps in methods.items()}
    dataset_tasks = {d: set().union(*(by_paper[p].get("tasks", set()) for p in ps)) for d, ps in datasets.items()}
    signals: list[GapSignal] = []
    for method, method_papers in sorted(methods.items()):
        if len(method_papers) < cfg.min_entity_support:
            continue
        for dataset, dataset_papers in sorted(datasets.items()):
            if len(dataset_papers) < cfg.min_entity_support or (method, dataset) in direct_md:
                continue
            shared_tasks = method_tasks[method] & dataset_tasks[dataset]
            for task in sorted(shared_tasks):
                signals.append(GapSignal(
                    signal_id=_stable_id("signal", ["missing_combination", "method-dataset-task", method, dataset, task]),
                    gap_type="missing_combination",
                    statement=f"Method '{method}' and dataset '{dataset}' are separately represented for task '{task}', but their direct combination is absent from the indexed corpus.",
                    paper_ids=sorted(method_papers | dataset_papers),
                    node_ids=[_entity_node_id("method", method), _entity_node_id("dataset", dataset), _entity_node_id("task", task)],
                    entity_values={"method": method, "dataset": dataset, "task": task},
                    support_count=min(len(method_papers), len(dataset_papers)),
                    structural_score=_mean_score(min(1.0, len(method_papers) / (2 * cfg.min_entity_support)), min(1.0, len(dataset_papers) / (2 * cfg.min_entity_support)), min(1.0, len(shared_tasks) / 2)),
                    provenance=["shared-task context"],
                ))
    for method, method_papers in sorted(methods.items()):
        if len(method_papers) < cfg.min_entity_support:
            continue
        method_datasets = set().union(*(by_paper[p].get("datasets", set()) for p in method_papers))
        for task, task_papers in sorted(tasks.items()):
            if len(task_papers) < cfg.min_entity_support or (method, task) in direct_mt:
                continue
            task_datasets = set().union(*(by_paper[p].get("datasets", set()) for p in task_papers))
            for dataset in sorted(method_datasets & task_datasets):
                signals.append(GapSignal(
                    signal_id=_stable_id("signal", ["missing_combination", "method-task", method, task, dataset]),
                    gap_type="missing_combination",
                    statement=f"Method '{method}' and task '{task}' are separately represented around dataset '{dataset}', but their direct combination is absent from the indexed corpus.",
                    paper_ids=sorted(method_papers | task_papers),
                    node_ids=[_entity_node_id("method", method), _entity_node_id("task", task), _entity_node_id("dataset", dataset)],
                    entity_values={"method": method, "task": task, "dataset": dataset},
                    support_count=min(len(method_papers), len(task_papers)),
                    structural_score=_mean_score(min(1.0, len(method_papers) / (2 * cfg.min_entity_support)), min(1.0, len(task_papers) / (2 * cfg.min_entity_support))),
                    provenance=["shared-dataset context"],
                ))
    signals = list({signal.signal_id: signal for signal in signals}.values())
    signals = sorted(signals, key=lambda s: (-s.structural_score, s.signal_id))[:cfg.max_candidates_per_type]
    return signals, [_candidate(s) for s in signals]


def _contradictions(claims: list[dict[str, object]], cfg: GapDiscoveryConfig) -> tuple[list[GapSignal], list[GapCandidate]]:
    groups: dict[str, dict[str, list[dict[str, object]]]] = defaultdict(lambda: {"positive": [], "negative": []})
    for claim in claims:
        if claim["claim_type"] != "result":
            continue
        text = str(claim["label"])
        positive, negative = _claim_polarity(text)
        if not positive and not negative:
            continue
        topic = _normalize(text)
        for marker in _POSITIVE | _NEGATIVE:
            topic = re.sub(rf"\b{re.escape(marker)}\b", " ", topic)
        for marker_pattern in _NEGATED_POSITIVE_PATTERNS:
            topic = re.sub(marker_pattern, " ", topic, flags=re.IGNORECASE)
        topic = _normalize(topic)
        if len(topic.split()) < 2:
            continue
        if positive:
            groups[topic]["positive"].append(claim)
        if negative:
            groups[topic]["negative"].append(claim)
    signals: list[GapSignal] = []
    for topic, polarities in sorted(groups.items()):
        positive_papers = {str(x["paper_id"]) for x in polarities["positive"]}
        negative_papers = {str(x["paper_id"]) for x in polarities["negative"]}
        papers = positive_papers | negative_papers
        if not positive_papers or not negative_papers or len(papers) < cfg.min_contradiction_support:
            continue
        signals.append(GapSignal(
            signal_id=_stable_id("signal", ["contradiction", topic]),
            gap_type="contradiction",
            statement=f"The indexed literature contains conflicting result claims around '{topic}'.",
            paper_ids=sorted(papers),
            node_ids=sorted({str(x["node_id"]) for x in polarities["positive"] + polarities["negative"]}),
            support_count=len(papers),
            structural_score=_mean_score(min(1.0, len(positive_papers) / cfg.min_contradiction_support), min(1.0, len(negative_papers) / cfg.min_contradiction_support)),
            provenance=["deterministic polarity markers", f"positive_papers={len(positive_papers)}", f"negative_papers={len(negative_papers)}"],
        ))
    signals = sorted(signals, key=lambda s: (-s.structural_score, s.signal_id))[:cfg.max_candidates_per_type]
    return signals, [_candidate(s) for s in signals]


def _underexplored_conditions(papers: list[sqlite3.Row], by_paper: dict[str, dict[str, set[str]]], cfg: GapDiscoveryConfig) -> tuple[list[GapSignal], list[GapCandidate]]:
    condition_support: defaultdict[str, set[str]] = defaultdict(set)
    for row in papers:
        try:
            metadata = json.loads(row["metadata_json"])
        except json.JSONDecodeError:
            metadata = {}
        for condition in _metadata_values(metadata, _CONDITION_KEYS):
            condition_support[condition].add(row["paper_id"])
    pair_papers: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    for paper_id, fields in by_paper.items():
        for method in fields.get("methods", set()):
            for task in fields.get("tasks", set()):
                pair_papers[(method, task)].add(paper_id)
    signals: list[GapSignal] = []
    for (method, task), relevant in sorted(pair_papers.items()):
        if len(relevant) < cfg.min_entity_support:
            continue
        context_papers = relevant
        for condition, condition_papers in sorted(condition_support.items()):
            if len(condition_papers) < cfg.min_condition_support:
                continue
            anchored = condition_papers & context_papers
            if not anchored:
                continue
            coverage = len(anchored) / len(relevant)
            if coverage > cfg.max_underexplored_coverage:
                continue
            signals.append(GapSignal(
                signal_id=_stable_id("signal", ["underexplored_condition", method, task, condition]),
                gap_type="underexplored_condition",
                statement=f"Condition '{condition}' is underrepresented for method '{method}' on task '{task}'.",
                paper_ids=sorted(relevant | condition_papers),
                node_ids=[_entity_node_id("method", method), _entity_node_id("task", task)],
                entity_values={"method": method, "task": task},
                support_count=len(anchored),
                structural_score=_mean_score(1.0 - coverage, min(1.0, len(relevant) / 5)),
                provenance=[f"condition_support={len(condition_papers)}", f"pair_support={len(relevant)}", f"pair_condition_coverage={coverage:.4f}"],
            ))
    signals = sorted(signals, key=lambda s: (-s.structural_score, s.signal_id))[:cfg.max_candidates_per_type]
    candidates = []
    for signal in signals:
        coverage = float(next(value.split("=", 1)[1] for value in signal.provenance if value.startswith("pair_condition_coverage=")))
        candidates.append(_candidate(signal, coverage=coverage))
    return signals, candidates


def _unresolved_limitations(claims: list[dict[str, object]], cfg: GapDiscoveryConfig) -> tuple[list[GapSignal], list[GapCandidate]]:
    groups: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
    for claim in claims:
        if claim["claim_type"] == "limitation":
            topic = _normalize(str(claim["label"]))
            if len(topic.split()) >= 2:
                groups[topic].append(claim)
    signals: list[GapSignal] = []
    for topic, items in sorted(groups.items()):
        papers = sorted({str(item["paper_id"]) for item in items})
        if len(papers) < cfg.min_limitation_support:
            continue
        signals.append(GapSignal(
            signal_id=_stable_id("signal", ["unresolved_limitation", topic]),
            gap_type="unresolved_limitation",
            statement=f"Limitation theme '{topic}' recurs across {len(papers)} indexed papers and is a candidate unresolved limitation.",
            paper_ids=papers,
            node_ids=sorted({str(item["node_id"]) for item in items}),
            support_count=len(papers),
            structural_score=min(1.0, len(papers) / (2 * cfg.min_limitation_support)),
            provenance=["recurring limitation claims"],
        ))
    signals = sorted(signals, key=lambda s: (-s.structural_score, s.signal_id))[:cfg.max_candidates_per_type]
    return signals, [_candidate(s) for s in signals]


def _cross_domain(papers: list[sqlite3.Row], by_paper: dict[str, dict[str, set[str]]], entity_papers: dict[str, dict[str, set[str]]], cfg: GapDiscoveryConfig) -> tuple[list[GapSignal], list[GapCandidate]]:
    method_domain: defaultdict[str, defaultdict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    task_domain: defaultdict[str, defaultdict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for row in papers:
        try:
            metadata = json.loads(row["metadata_json"])
        except json.JSONDecodeError:
            metadata = {}
        domains = _metadata_values(metadata, _DOMAIN_KEYS)
        paper_id = row["paper_id"]
        for method in by_paper[paper_id].get("methods", set()):
            for domain in domains:
                method_domain[method][domain].add(paper_id)
        for task in by_paper[paper_id].get("tasks", set()):
            for domain in domains:
                task_domain[task][domain].add(paper_id)
    signals: list[GapSignal] = []
    for method in sorted(entity_papers["methods"]):
        for task in sorted(entity_papers["tasks"]):
            if entity_papers["methods"][method] & entity_papers["tasks"][task]:
                continue
            for method_domain, method_domain_papers in sorted(method_domain[method].items()):
                if len(method_domain_papers) < cfg.min_entity_support:
                    continue
                for task_domain, task_domain_papers in sorted(task_domain[task].items()):
                    if method_domain == task_domain or len(task_domain_papers) < cfg.min_entity_support:
                        continue
                    signals.append(GapSignal(
                        signal_id=_stable_id("signal", ["cross_domain", method, task, method_domain, task_domain]),
                        gap_type="cross_domain",
                        statement=f"Method '{method}' is represented in domain '{method_domain}' while task '{task}' is represented in domain '{task_domain}', but the direct combination is absent from the indexed corpus.",
                        paper_ids=sorted(method_domain_papers | task_domain_papers),
                        node_ids=[_entity_node_id("method", method), _entity_node_id("task", task)],
                        entity_values={"method": method, "task": task},
                        support_count=min(len(method_domain_papers), len(task_domain_papers)),
                        structural_score=_mean_score(min(1.0, len(method_domain_papers) / (2 * cfg.min_entity_support)), min(1.0, len(task_domain_papers) / (2 * cfg.min_entity_support))),
                        provenance=[f"method_domain={method_domain}", f"task_domain={task_domain}"],
                    ))
    signals = sorted(signals, key=lambda s: (-s.structural_score, s.signal_id))[:cfg.max_candidates_per_type]
    return signals, [_candidate(s) for s in signals]


def _graph_negative_space(by_paper: dict[str, dict[str, set[str]]], entity_papers: dict[str, dict[str, set[str]]], cfg: GapDiscoveryConfig) -> tuple[list[GapSignal], list[GapCandidate]]:
    method_tasks: defaultdict[str, set[str]] = defaultdict(set)
    dataset_tasks: defaultdict[str, set[str]] = defaultdict(set)
    direct_md: set[tuple[str, str]] = set()
    for fields in by_paper.values():
        methods, datasets, tasks = fields.get("methods", set()), fields.get("datasets", set()), fields.get("tasks", set())
        for method in methods:
            method_tasks[method].update(tasks)
        for dataset in datasets:
            dataset_tasks[dataset].update(tasks)
        for method in methods:
            for dataset in datasets:
                direct_md.add((method, dataset))
    signals: list[GapSignal] = []
    for method, method_neighbors in sorted(method_tasks.items()):
        if len(method_neighbors) < cfg.min_graph_degree:
            continue
        for dataset, dataset_neighbors in sorted(dataset_tasks.items()):
            if len(dataset_neighbors) < cfg.min_graph_degree or (method, dataset) in direct_md:
                continue
            common_tasks = sorted(method_neighbors & dataset_neighbors)
            if len(common_tasks) < cfg.min_common_neighbors:
                continue
            signals.append(GapSignal(
                signal_id=_stable_id("signal", ["graph_negative_space", method, dataset, *common_tasks]),
                gap_type="graph_negative_space",
                statement=f"Method '{method}' and dataset '{dataset}' are structurally separated: they share {len(common_tasks)} task neighbors but have no direct indexed co-occurrence.",
                paper_ids=sorted(entity_papers["methods"][method] | entity_papers["datasets"][dataset]),
                node_ids=[_entity_node_id("method", method), _entity_node_id("dataset", dataset)] + [_entity_node_id("task", task) for task in common_tasks],
                entity_values={"method": method, "dataset": dataset},
                support_count=len(common_tasks),
                structural_score=_mean_score(min(1.0, len(common_tasks) / (2 * cfg.min_common_neighbors)), min(1.0, len(method_neighbors) / (2 * cfg.min_graph_degree)), min(1.0, len(dataset_neighbors) / (2 * cfg.min_graph_degree))),
                provenance=["common-neighbor structural-hole analysis"],
            ))
    signals = sorted(signals, key=lambda s: (-s.structural_score, s.signal_id))[:cfg.max_candidates_per_type]
    return signals, [_candidate(s) for s in signals]


def _fingerprint(papers: list[sqlite3.Row], by_paper: dict[str, dict[str, set[str]]], claims: list[dict[str, object]]) -> str:
    payload = {
        "papers": [{"paper_id": row["paper_id"], "year": row["year"], "source": row["source"], "metadata": row["metadata_json"]} for row in papers],
        "entities": {paper_id: {field: sorted(values) for field, values in sorted(fields.items())} for paper_id, fields in sorted(by_paper.items())},
        "claims": claims,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def discover_gaps(world: ScientificWorldModel, config: GapDiscoveryConfig | None = None) -> GapDiscoveryResult:
    """Run deterministic Phase 4 discovery and emit candidate gaps only."""
    cfg = config or GapDiscoveryConfig()
    papers, by_paper, entity_papers = _load_snapshot(world, cfg.temporal_cutoff)
    allowed = {row["paper_id"] for row in papers}
    claims = _load_claims(world, allowed)
    run_id = _stable_id("gap-run", [json.dumps(cfg.model_dump(mode="json"), sort_keys=True, separators=(",", ":")), _fingerprint(papers, by_paper, claims)])
    detectors = {
        "missing_combination": lambda: _missing_combinations(by_paper, entity_papers, cfg),
        "contradiction": lambda: _contradictions(claims, cfg),
        "underexplored_condition": lambda: _underexplored_conditions(papers, by_paper, cfg),
        "unresolved_limitation": lambda: _unresolved_limitations(claims, cfg),
        "cross_domain": lambda: _cross_domain(papers, by_paper, entity_papers, cfg),
        "graph_negative_space": lambda: _graph_negative_space(by_paper, entity_papers, cfg),
    }
    signals: list[GapSignal] = []
    candidates: list[GapCandidate] = []
    for gap_type, detector in detectors.items():
        if gap_type not in cfg.include_types:
            continue
        detected_signals, detected_candidates = detector()
        signals.extend(detected_signals)
        candidates.extend(detected_candidates)
    signals.sort(key=lambda item: (item.gap_type, -item.structural_score, item.signal_id))
    candidates.sort(key=lambda item: (-item.confidence, item.gap_type, item.gap_id))
    return GapDiscoveryResult(run_id=run_id, temporal_cutoff=cfg.temporal_cutoff, corpus_paper_count=len(papers), signals=signals, candidates=candidates)
