"""Deterministic Phase 4 research-gap discovery over the scientific world model."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import defaultdict
from typing import Iterable

from agentic_research.schemas.gap import GapCandidate
from agentic_research.schemas.phase4 import GapDiscoveryConfig, GapDiscoveryResult, GapSignal, GapSignalType
from agentic_research.world_model.store import ScientificWorldModel

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "it", "of", "on", "or", "that", "the", "their", "this", "to", "with",
    "we", "our", "using", "used", "use", "show", "shows", "results", "result",
    "method", "approach", "model", "study", "paper", "performance", "significantly",
}
_POSITIVE = {
    "improve", "improves", "improved", "improving", "increase", "increases", "increased",
    "higher", "better", "outperform", "outperforms", "outperformed", "boost", "boosts",
    "benefit", "benefits", "effective", "significant", "wins", "gain", "gains",
}
_NEGATIVE = {
    "decrease", "decreases", "decreased", "lower", "lowers", "worse", "underperform",
    "underperforms", "harm", "harms", "hurt", "hurts", "degrade", "degrades", "failure",
    "fails", "failed", "ineffective", "insignificant", "no", "not", "without",
}
_CONDITION_KEYS = {
    "condition", "conditions", "setting", "settings", "language", "languages", "modality",
    "modalities", "resource", "resources", "resource_regime", "data_regime", "regime",
    "population", "environment", "hardware", "scale", "data_scale", "dataset_scale",
}
_DOMAIN_KEYS = {"domain", "domains", "field", "fields", "application_domain", "application_domains"}


def _normalize(text: str) -> str:
    tokens = re.findall(r"\w+", text.lower(), flags=re.UNICODE)
    return " ".join(token for token in tokens if token not in _STOPWORDS and len(token) > 1)


def _tokens(text: str) -> set[str]:
    return set(_normalize(text).split())


def _stable_id(prefix: str, parts: Iterable[str]) -> str:
    material = "||".join(parts)
    digest = hashlib.sha1(material.encode("utf-8")).hexdigest()[:20]
    return f"{prefix}:{digest}"


def _score(*values: float) -> float:
    if not values:
        return 0.0
    value = sum(values) / len(values)
    return max(0.0, min(1.0, value))


def _iter_strings(value: object) -> Iterable[str]:
    if isinstance(value, str) and value.strip():
        yield value.strip()
    elif isinstance(value, list):
        for item in value:
            yield from _iter_strings(item)


def _metadata_values(metadata: dict[str, object], keys: set[str]) -> set[str]:
    values: set[str] = set()
    for key, value in metadata.items():
        if key.lower() in keys:
            values.update(v for v in _iter_strings(value) if len(v) <= 200)
    return {_normalize(value) for value in values if _normalize(value)}


def _paper_snapshot(world: ScientificWorldModel, cutoff: int | None) -> tuple[list[sqlite3.Row], dict[str, dict[str, set[str]]], dict[str, dict[str, set[str]]]]:
    rows = world.connection.execute(
        "SELECT paper_id,title,year,source,metadata_json FROM papers ORDER BY paper_id"
    ).fetchall()
    papers = [row for row in rows if cutoff is None or (row["year"] is not None and row["year"] <= cutoff)]
    allowed = {row["paper_id"] for row in papers}

    by_paper: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    entity_papers: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    query = """
        SELECT e.source_id, e.target_id, e.edge_type, n.node_type, n.label
        FROM edges e
        JOIN nodes n ON n.node_id=e.target_id
        WHERE e.edge_type IN ('has_method','has_dataset','has_task','has_metric','has_baseline')
    """
    for row in world.connection.execute(query).fetchall():
        if not row["source_id"].startswith("paper:"):
            continue
        paper_id = row["source_id"][len("paper:"):]
        if paper_id not in allowed:
            continue
        field = {
            "has_method": "methods",
            "has_dataset": "datasets",
            "has_task": "tasks",
            "has_metric": "metrics",
            "has_baseline": "baselines",
        }[row["edge_type"]]
        value = _normalize(row["label"])
        if value:
            by_paper[paper_id][field].add(value)
            entity_papers[field][value].add(paper_id)
    return papers, by_paper, entity_papers


def _claim_snapshot(world: ScientificWorldModel, allowed: set[str]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for row in world.connection.execute(
        "SELECT node_id,paper_id,label,payload_json FROM nodes WHERE node_type='claim' AND paper_id IS NOT NULL"
    ).fetchall():
        if row["paper_id"] not in allowed:
            continue
        try:
            payload = json.loads(row["payload_json"])
        except json.JSONDecodeError:
            payload = {}
        records.append(
            {
                "node_id": row["node_id"],
                "paper_id": row["paper_id"],
                "label": row["label"],
                "claim_type": payload.get("claim_type", ""),
            }
        )
    return records


def _make_candidate(
    *,
    signal: GapSignal,
    method: str | None = None,
    task: str | None = None,
    dataset: str | None = None,
    coverage_ratio: float | None = None,
    confidence: float | None = None,
) -> GapCandidate:
    structural = signal.structural_score
    final_confidence = structural if confidence is None else confidence
    return GapCandidate(
        gap_id=_stable_id("gap", [signal.signal_id]),
        gap_type=signal.gap_type,
        statement=signal.statement,
        method=method,
        task=task,
        dataset=dataset,
        evidence_paper_ids=sorted(set(signal.paper_ids)),
        search_queries=[signal.statement],
        signal_ids=[signal.signal_id],
        support_count=signal.support_count,
        coverage_ratio=coverage_ratio,
        structural_support=structural,
        confidence=max(0.0, min(1.0, final_confidence)),
        status="candidate",
        rationale=(
            "Deterministic structural signal from the indexed corpus. "
            "This is a candidate only; Phase 4 does not verify novelty or rule out prior work."
        ),
    )


def _missing_combinations(
    by_paper: dict[str, dict[str, set[str]]],
    entity_papers: dict[str, dict[str, set[str]]],
    config: GapDiscoveryConfig,
) -> tuple[list[GapSignal], list[GapCandidate]]:
    signals: list[GapSignal] = []
    pairs: list[tuple[str, str, str | None, str]] = []

    methods = entity_papers["methods"]
    datasets = entity_papers["datasets"]
    tasks = entity_papers["tasks"]

    for method, method_papers in sorted(methods.items()):
        if len(method_papers) < config.min_entity_support:
            continue
        for dataset, dataset_papers in sorted(datasets.items()):
            if len(dataset_papers) < config.min_entity_support or method_papers & dataset_papers:
                continue
            common_papers = method_papers | dataset_papers
            pairs.append((method, dataset, None, "method_dataset"))
            task_support = defaultdict(set)
            for paper_id in common_papers:
                for task in by_paper[paper_id].get("tasks", set()):
                    task_support[task].add(paper_id)
            for task, support in sorted(task_support.items()):
                if len(support) >= config.min_entity_support and not any(
                    method in by_paper[p].get("methods", set()) and dataset in by_paper[p].get("datasets", set())
                    for p in by_paper
                    if task in by_paper[p].get("tasks", set())
                ):
                    pairs.append((method, dataset, task, "method_dataset_task"))

    for method, method_papers in sorted(methods.items()):
        if len(method_papers) < config.min_entity_support:
            continue
        for task, task_papers in sorted(tasks.items()):
            if len(task_papers) < config.min_entity_support or method_papers & task_papers:
                continue
            pairs.append((method, "", task, "method_task"))

    seen: set[tuple[str, str, str | None]] = set()
    for method, dataset, task, subtype in pairs:
        key = (method, dataset, task)
        if key in seen:
            continue
        seen.add(key)
        statement = (
            f"Method '{method}' and dataset '{dataset}' are both established in the indexed corpus, "
            f"but their combination is not observed"
            + (f" for task '{task}'" if task else "")
            + "."
        )
        signal = GapSignal(
            signal_id=_stable_id("signal", ["missing_combination", method, dataset, task or "", subtype]),
            gap_type="missing_combination",
            statement=statement,
            paper_ids=sorted(entity_papers["methods"][method] | entity_papers["datasets"][dataset]),
            node_ids=[f"method:{method}", f"dataset:{dataset}"] + ([f"task:{task}"] if task else []),
            support_count=min(len(entity_papers["methods"][method]), len(entity_papers["datasets"][dataset])),
            structural_score=_score(
                min(1.0, len(entity_papers["methods"][method]) / (2 * config.min_entity_support)),
                min(1.0, len(entity_papers["datasets"][dataset]) / (2 * config.min_entity_support)),
            ),
            provenance=[subtype],
        )
        signals.append(signal)
        if len([s for s in signals if s.gap_type == "missing_combination"]) >= config.max_candidates_per_type:
            break
    candidates = [_make_candidate(signal=signal, method=next((part for part in signal.node_ids if part.startswith("method:")), "")[len("method:"):] or None,
                                  dataset=next((part for part in signal.node_ids if part.startswith("dataset:")), "")[len("dataset:"):] or None,
                                  task=next((part for part in signal.node_ids if part.startswith("task:")), "")[len("task:"):] or None)
                  for signal in signals]
    return signals, candidates


def _contradictions(claims: list[dict[str, object]], config: GapDiscoveryConfig) -> tuple[list[GapSignal], list[GapCandidate]]:
    groups: dict[str, dict[str, list[dict[str, object]]]] = defaultdict(lambda: {"positive": [], "negative": []})
    for claim in claims:
        if claim["claim_type"] != "result":
            continue
        text = str(claim["label"])
        tokens = _tokens(text)
        has_positive = bool(tokens & _POSITIVE)
        has_negative = bool(tokens & _NEGATIVE)
        if not has_positive and not has_negative:
            continue
        topic = _normalize(text)
        for token in _POSITIVE | _NEGATIVE:
            topic = re.sub(rf"\b{re.escape(token)}\b", " ", topic)
        topic = _normalize(topic)
        if len(topic.split()) < 2:
            continue
        if has_positive:
            groups[topic]["positive"].append(claim)
        if has_negative:
            groups[topic]["negative"].append(claim)

    signals: list[GapSignal] = []
    for topic, polarities in sorted(groups.items()):
        positive_papers = {str(item["paper_id"]) for item in polarities["positive"]}
        negative_papers = {str(item["paper_id"]) for item in polarities["negative"]}
        if not positive_papers or not negative_papers or len(positive_papers | negative_papers) < config.min_contradiction_support:
            continue
        papers = sorted(positive_papers | negative_papers)
        statement = f"The indexed literature contains conflicting result claims around '{topic}'."
        support = len(papers)
        signal = GapSignal(
            signal_id=_stable_id("signal", ["contradiction", topic]),
            gap_type="contradiction",
            statement=statement,
            paper_ids=papers,
            node_ids=sorted({str(item["node_id"]) for item in polarities["positive"] + polarities["negative"]}),
            support_count=support,
            structural_score=_score(min(1.0, support / 4), 1.0 if len(positive_papers) > 0 and len(negative_papers) > 0 else 0.0),
            provenance=["result_claim_polarity", f"positive_papers={len(positive_papers)}", f"negative_papers={len(negative_papers)}"],
        )
        signals.append(signal)
        if len([s for s in signals if s.gap_type == "contradiction"]) >= config.max_candidates_per_type:
            break
    return signals, [_make_candidate(signal=s) for s in signals]


def _conditions(
    papers: list[sqlite3.Row],
    by_paper: dict[str, dict[str, set[str]]],
    config: GapDiscoveryConfig,
) -> tuple[list[GapSignal], list[GapCandidate]]:
    condition_by_paper: dict[str, set[str]] = defaultdict(set)
    global_support: defaultdict[str, set[str]] = defaultdict(set)
    for row in papers:
        try:
            metadata = json.loads(row["metadata_json"])
        except json.JSONDecodeError:
            metadata = {}
        values = _metadata_values(metadata, _CONDITION_KEYS)
        condition_by_paper[row["paper_id"]].update(values)
        for value in values:
            global_support[value].add(row["paper_id"])

    pair_papers: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    for paper_id, fields in by_paper.items():
        for method in fields.get("methods", set()):
            for task in fields.get("tasks", set()):
                pair_papers[(method, task)].add(paper_id)

    signals: list[GapSignal] = []
    for (method, task), relevant in sorted(pair_papers.items()):
        if len(relevant) < config.min_entity_support:
            continue
        for condition, all_condition_papers in sorted(global_support.items()):
            if len(all_condition_papers) < config.min_condition_support:
                continue
            covered = relevant & all_condition_papers
            coverage = len(covered) / len(relevant)
            if coverage == 0 or coverage > config.max_underexplored_coverage:
                continue
            statement = f"Condition '{condition}' is underrepresented for method '{method}' on task '{task}'."
            signal = GapSignal(
                signal_id=_stable_id("signal", ["underexplored_condition", method, task, condition]),
                gap_type="underexplored_condition",
                statement=statement,
                paper_ids=sorted(relevant | all_condition_papers),
                node_ids=[f"method:{method}", f"task:{task}"],
                support_count=len(covered),
                structural_score=_score(1.0 - coverage, min(1.0, len(relevant) / 5)),
                provenance=[f"condition_support={len(all_condition_papers)}", f"pair_support={len(relevant)}", f"pair_condition_coverage={coverage:.4f}"],
            )
            signals.append(signal)
            if len([s for s in signals if s.gap_type == "underexplored_condition"]) >= config.max_candidates_per_type:
                break
    candidates = []
    for signal in signals:
        method = signal.node_ids[0].split(":", 1)[1]
        task = signal.node_ids[1].split(":", 1)[1]
        condition = signal.statement.split("Condition '", 1)[1].split("' is", 1)[0]
        coverage = float(next(x.split("=", 1)[1] for x in signal.provenance if x.startswith("pair_condition_coverage=")))
        candidates.append(_make_candidate(signal=signal, method=method, task=task, coverage_ratio=coverage))
    return signals, candidates


def _limitations(claims: list[dict[str, object]], config: GapDiscoveryConfig) -> tuple[list[GapSignal], list[GapCandidate]]:
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for claim in claims:
        if claim["claim_type"] != "limitation":
            continue
        topic = _normalize(str(claim["label"]))
        if len(topic.split()) < 2:
            continue
        groups[topic].append(claim)

    signals: list[GapSignal] = []
    for topic, items in sorted(groups.items()):
        papers = sorted({str(item["paper_id"]) for item in items})
        if len(papers) < config.min_limitation_support:
            continue
        statement = f"Limitation theme '{topic}' recurs across {len(papers)} indexed papers and is a candidate unresolved limitation."
        signal = GapSignal(
            signal_id=_stable_id("signal", ["unresolved_limitation", topic]),
            gap_type="unresolved_limitation",
            statement=statement,
            paper_ids=papers,
            node_ids=sorted({str(item["node_id"]) for item in items}),
            support_count=len(papers),
            structural_score=min(1.0, len(papers) / (config.min_limitation_support * 2)),
            provenance=["recurring_limitation_claim"],
        )
        signals.append(signal)
        if len([s for s in signals if s.gap_type == "unresolved_limitation"]) >= config.max_candidates_per_type:
            break
    return signals, [_make_candidate(signal=s) for s in signals]


def _cross_domain(
    papers: list[sqlite3.Row],
    by_paper: dict[str, dict[str, set[str]]],
    entity_papers: dict[str, dict[str, set[str]]],
    config: GapDiscoveryConfig,
) -> tuple[list[GapSignal], list[GapCandidate]]:
    domain_by_paper: dict[str, set[str]] = defaultdict(set)
    method_domain: defaultdict[str, defaultdict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    task_domain: defaultdict[str, defaultdict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for row in papers:
        try:
            metadata = json.loads(row["metadata_json"])
        except json.JSONDecodeError:
            metadata = {}
        domains = _metadata_values(metadata, _DOMAIN_KEYS)
        domain_by_paper[row["paper_id"]].update(domains)
        for method in by_paper[row["paper_id"]].get("methods", set()):
            for domain in domains:
                method_domain[method][domain].add(row["paper_id"])
        for task in by_paper[row["paper_id"]].get("tasks", set()):
            for domain in domains:
                task_domain[task][domain].add(row["paper_id"])

    signals: list[GapSignal] = []
    for method in sorted(entity_papers["methods"]):
        for task in sorted(entity_papers["tasks"]):
            combined = entity_papers["methods"][method] & entity_papers["tasks"][task]
            if combined:
                continue
            for method_domain_name, method_papers in sorted(method_domain[method].items()):
                if len(method_papers) < config.min_entity_support:
                    continue
                for task_domain_name, task_papers in sorted(task_domain[task].items()):
                    if method_domain_name == task_domain_name or len(task_papers) < config.min_entity_support:
                        continue
                    statement = (
                        f"Method '{method}' is represented in domain '{method_domain_name}' while task '{task}' "
                        f"is represented in domain '{task_domain_name}', but the indexed corpus contains no direct combination."
                    )
                    signal = GapSignal(
                        signal_id=_stable_id("signal", ["cross_domain", method, task, method_domain_name, task_domain_name]),
                        gap_type="cross_domain",
                        statement=statement,
                        paper_ids=sorted(method_papers | task_papers),
                        node_ids=[f"method:{method}", f"task:{task}"],
                        support_count=min(len(method_papers), len(task_papers)),
                        structural_score=_score(
                            min(1.0, len(method_papers) / (2 * config.min_entity_support)),
                            min(1.0, len(task_papers) / (2 * config.min_entity_support)),
                        ),
                        provenance=[f"method_domain={method_domain_name}", f"task_domain={task_domain_name}"],
                    )
                    signals.append(signal)
                    if len([s for s in signals if s.gap_type == "cross_domain"]) >= config.max_candidates_per_type:
                        return signals, [_make_candidate(signal=s) for s in signals]
    return signals, [_make_candidate(signal=s, method=s.node_ids[0].split(":", 1)[1], task=s.node_ids[1].split(":", 1)[1]) for s in signals]


def _graph_negative_space(
    by_paper: dict[str, dict[str, set[str]]],
    entity_papers: dict[str, dict[str, set[str]]],
    config: GapDiscoveryConfig,
) -> tuple[list[GapSignal], list[GapCandidate]]:
    method_tasks: defaultdict[str, set[str]] = defaultdict(set)
    dataset_tasks: defaultdict[str, set[str]] = defaultdict(set)
    method_datasets: set[tuple[str, str]] = set()
    for paper_id, fields in by_paper.items():
        methods = fields.get("methods", set())
        datasets = fields.get("datasets", set())
        tasks = fields.get("tasks", set())
        for method in methods:
            method_tasks[method].update(tasks)
        for dataset in datasets:
            dataset_tasks[dataset].update(tasks)
        for method in methods:
            for dataset in datasets:
                method_datasets.add((method, dataset))

    signals: list[GapSignal] = []
    for method, tasks_for_method in sorted(method_tasks.items()):
        if len(tasks_for_method) < config.min_graph_degree:
            continue
        for dataset, tasks_for_dataset in sorted(dataset_tasks.items()):
            if len(tasks_for_dataset) < config.min_graph_degree or (method, dataset) in method_datasets:
                continue
            common = sorted(tasks_for_method & tasks_for_dataset)
            if len(common) < config.min_common_neighbors:
                continue
            statement = (
                f"Method '{method}' and dataset '{dataset}' form a graph negative-space candidate: "
                f"they share {len(common)} task neighbors ({', '.join(common[:5])}) but have no direct indexed co-occurrence."
            )
            signal = GapSignal(
                signal_id=_stable_id("signal", ["graph_negative_space", method, dataset, *common]),
                gap_type="graph_negative_space",
                statement=statement,
                paper_ids=sorted(entity_papers["methods"][method] | entity_papers["datasets"][dataset]),
                node_ids=[f"method:{method}", f"dataset:{dataset}"] + [f"task:{task}" for task in common],
                support_count=len(common),
                structural_score=_score(
                    min(1.0, len(common) / (config.min_common_neighbors * 2)),
                    min(1.0, len(tasks_for_method) / (config.min_graph_degree * 2)),
                    min(1.0, len(tasks_for_dataset) / (config.min_graph_degree * 2)),
                ),
                provenance=["common-neighbor structural-hole analysis"],
            )
            signals.append(signal)
            if len([s for s in signals if s.gap_type == "graph_negative_space"]) >= config.max_candidates_per_type:
                break
    candidates = [
        _make_candidate(
            signal=s,
            method=s.node_ids[0].split(":", 1)[1],
            dataset=s.node_ids[1].split(":", 1)[1],
        )
        for s in signals
    ]
    return signals, candidates


def discover_gaps(world: ScientificWorldModel, config: GapDiscoveryConfig | None = None) -> GapDiscoveryResult:
    """Run all Phase 4 deterministic gap detectors over the indexed world model.

    The function never performs novelty verification and never changes a gap's
    status away from ``candidate``. Phase 5 is responsible for adversarial review.
    """

    cfg = config or GapDiscoveryConfig()
    papers, by_paper, entity_papers = _paper_snapshot(world, cfg.temporal_cutoff)
    allowed = {row["paper_id"] for row in papers}
    claims = _claim_snapshot(world, allowed)
    paper_ids = sorted(allowed)
    run_id = _stable_id("gap-run", [str(cfg.model_dump(mode="json")), *paper_ids])

    all_signals: list[GapSignal] = []
    all_candidates: list[GapCandidate] = []
    detectors = {
        "missing_combination": lambda: _missing_combinations(by_paper, entity_papers, cfg),
        "contradiction": lambda: _contradictions(claims, cfg),
        "underexplored_condition": lambda: _conditions(papers, by_paper, cfg),
        "unresolved_limitation": lambda: _limitations(claims, cfg),
        "cross_domain": lambda: _cross_domain(papers, by_paper, entity_papers, cfg),
        "graph_negative_space": lambda: _graph_negative_space(by_paper, entity_papers, cfg),
    }
    for gap_type, detector in detectors.items():
        if gap_type not in cfg.include_types:
            continue
        signals, candidates = detector()
        all_signals.extend(signals)
        all_candidates.extend(candidates)

    all_signals.sort(key=lambda item: (item.gap_type, -item.structural_score, item.signal_id))
    all_candidates.sort(key=lambda item: (-item.confidence, item.gap_type, item.gap_id))
    return GapDiscoveryResult(
        run_id=run_id,
        temporal_cutoff=cfg.temporal_cutoff,
        corpus_paper_count=len(papers),
        signals=all_signals,
        candidates=all_candidates,
    )
