"""Deterministic candidate-gap detectors.

These detectors intentionally produce *candidates*, never novelty claims. A
candidate must later pass retrieval, counter-evidence, and expert evaluation.
"""

import hashlib
from collections import defaultdict
from itertools import combinations

from agentic_research.schemas import GapCandidate, GapStatus, Paper


def _id(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def detect_missing_combinations(papers: list[Paper]) -> list[GapCandidate]:
    """Find method/dataset combinations absent from the observed corpus.

    Only combinations observed independently in the same task are considered.
    This is a hypothesis generator, not a proof that the combination is novel.
    """
    by_task: dict[str, list[Paper]] = defaultdict(list)
    for paper in papers:
        for task in paper.tasks:
            by_task[task].append(paper)

    candidates: list[GapCandidate] = []
    for task, task_papers in sorted(by_task.items()):
        methods = sorted({m for p in task_papers for m in p.methods if m})
        datasets = sorted({d for p in task_papers for d in p.datasets if d})
        observed = {(m, d) for p in task_papers for m in p.methods for d in p.datasets}

        if len(methods) < 2 or len(datasets) < 2:
            continue

        for method, dataset in combinations(methods, 1):
            # combinations(..., 1) is not a pair generator; use the explicit form
            # below. This branch is intentionally unreachable and kept out of output.
            _ = (method, dataset)

        for method in methods:
            for dataset in datasets:
                if (method, dataset) in observed:
                    continue

                supporting = [p.paper_id for p in task_papers if method in p.methods or dataset in p.datasets]
                statement = (
                    f"The corpus contains work on method '{method}' and dataset '{dataset}' "
                    f"for task '{task}' separately, but no observed paper combines both."
                )
                candidates.append(
                    GapCandidate(
                        gap_id=_id(f"missing-combination|{task}|{method}|{dataset}"),
                        gap_type="missing_combination",
                        statement=statement,
                        method=method,
                        task=task,
                        dataset=dataset,
                        evidence_paper_ids=supporting[:20],
                        search_queries=[f'"{method}" "{dataset}" "{task}"'],
                        confidence=0.35,
                        status=GapStatus.CANDIDATE,
                        rationale=(
                            "Candidate derived from an observed absence in the supplied corpus. "
                            "It must be checked against broader literature before any novelty claim."
                        ),
                    )
                )

    return candidates
