"""Experiment search-tree construction and deterministic branching."""
from __future__ import annotations

import hashlib
from typing import Literal

from agentic_research.schemas.phase7 import ExperimentNode, ExperimentResult, ExperimentSearchTree, ExperimentSpec

TreeRelation = Literal["mutation", "ablation", "replication", "branch"]


def _id(*parts: str) -> str:
    return hashlib.sha256("||".join(parts).encode("utf-8")).hexdigest()[:20]


def create_tree(spec: ExperimentSpec) -> ExperimentSearchTree:
    node = ExperimentNode(
        node_id=f"node:{_id(spec.experiment_id)}",
        experiment_id=spec.experiment_id,
        parent_node_id=None,
        generation=0,
        relation="initial",
        status="planned",
    )
    return ExperimentSearchTree(
        tree_id=f"tree:{_id(spec.hypothesis_id, spec.experiment_id)}",
        hypothesis_id=spec.hypothesis_id,
        root_experiment_id=spec.experiment_id,
        nodes=[node],
        terminal_node_ids=[],
    )


def append_result(tree: ExperimentSearchTree, result: ExperimentResult, relation: TreeRelation = "replication") -> ExperimentSearchTree:
    parent = next(
        (node for node in reversed(tree.nodes) if node.status in {"planned", "running", "succeeded"}),
        tree.nodes[-1],
    )
    node = ExperimentNode(
        node_id=f"node:{_id(result.experiment_id, result.result_id)}",
        experiment_id=result.experiment_id,
        parent_node_id=parent.node_id,
        generation=parent.generation + 1,
        relation=relation,
        status=result.status,
        result_id=result.result_id,
    )
    nodes = [*tree.nodes, node]
    terminals = set(tree.terminal_node_ids)
    terminals.discard(parent.node_id)
    if result.status in {"failed", "timeout", "rejected", "cancelled"}:
        terminals.add(node.node_id)
    return tree.model_copy(update={"nodes": nodes, "terminal_node_ids": sorted(terminals)})
