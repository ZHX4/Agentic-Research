"""Deterministic hypothesis clustering and diversity utilities."""
from __future__ import annotations

from collections import deque

from .engine import _sim
from agentic_research.schemas.phase6 import HypothesisCandidate


def cluster_hypotheses(items: list[HypothesisCandidate], threshold: float = 0.70) -> list[list[HypothesisCandidate]]:
    """Return deterministic connected-component clusters by statement similarity."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0 and 1")
    ordered = sorted(items, key=lambda item: item.hypothesis.hypothesis_id)
    by_id = {item.hypothesis.hypothesis_id: item for item in ordered}
    remaining = set(by_id)
    clusters: list[list[HypothesisCandidate]] = []
    while remaining:
        start_id = min(remaining)
        queue = deque([start_id])
        remaining.remove(start_id)
        component: list[HypothesisCandidate] = []
        while queue:
            current_id = queue.popleft()
            current = by_id[current_id]
            component.append(current)
            neighbors = sorted(
                item.hypothesis.hypothesis_id
                for item in (by_id[identifier] for identifier in remaining)
                if _sim(current.hypothesis.statement, item.hypothesis.statement) >= threshold
            )
            for neighbor_id in neighbors:
                remaining.remove(neighbor_id)
                queue.append(neighbor_id)
        clusters.append(sorted(component, key=lambda item: item.hypothesis.hypothesis_id))
    return sorted(clusters, key=lambda group: group[0].hypothesis.hypothesis_id)
