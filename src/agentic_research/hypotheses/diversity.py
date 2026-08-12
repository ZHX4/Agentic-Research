"""Deterministic hypothesis clustering."""
from __future__ import annotations
import re
from collections import deque
from agentic_research.schemas.phase6 import HypothesisCandidate


def similarity(a: str, b: str) -> float:
    x = set(re.findall(r"\w+", a.casefold(), flags=re.UNICODE)); y = set(re.findall(r"\w+", b.casefold(), flags=re.UNICODE))
    return 1.0 if not x and not y else 0.0 if not x or not y else len(x & y) / len(x | y)


def cluster_hypotheses(items: list[HypothesisCandidate], threshold: float = 0.70) -> list[list[HypothesisCandidate]]:
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0 and 1")
    by_id = {x.hypothesis.hypothesis_id: x for x in items}; remaining = set(by_id); clusters: list[list[HypothesisCandidate]] = []
    while remaining:
        start = min(remaining); queue = deque([start]); remaining.remove(start); group: list[HypothesisCandidate] = []
        while queue:
            current = by_id[queue.popleft()]; group.append(current)
            neighbors = sorted(i for i in remaining if similarity(current.hypothesis.statement, by_id[i].hypothesis.statement) >= threshold)
            for neighbor in neighbors:
                remaining.remove(neighbor); queue.append(neighbor)
        clusters.append(sorted(group, key=lambda x: x.hypothesis.hypothesis_id))
    return sorted(clusters, key=lambda g: g[0].hypothesis.hypothesis_id)
