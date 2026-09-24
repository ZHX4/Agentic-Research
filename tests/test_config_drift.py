"""Drift guard: configs/default.yaml mirrors code defaults.

The YAML file is reference documentation, not runtime configuration (nothing
loads it). This test fails if the documented values drift from the
authoritative code defaults, forcing an explicit decision about which side
is correct. Safety properties themselves are enforced in code and covered
by phase tests; only duplicated scalar defaults are pinned here.
"""

from __future__ import annotations

import inspect
import tomllib
from pathlib import Path
from typing import Any, cast

import yaml
from pydantic import BaseModel

from agentic_research import __version__
from agentic_research.evaluation.comparison import compare_baselines
from agentic_research.evaluation.engine import evaluate_retrieval
from agentic_research.evaluation.metrics import bootstrap_mean_ci
from agentic_research.execution.planner import build_experiment_spec
from agentic_research.literature.settings import LiteratureSettings
from agentic_research.retrieval.hybrid import HybridRetriever
from agentic_research.schemas.gap import GapStatus
from agentic_research.schemas.phase4 import GapDiscoveryConfig
from agentic_research.schemas.phase5 import NoveltyVerificationConfig
from agentic_research.schemas.phase6 import HypothesisConfig
from agentic_research.schemas.phase7 import SandboxPolicy
from agentic_research.schemas.phase9 import AutonomousRunConfig

ROOT = Path(__file__).resolve().parent.parent


def _config() -> dict[str, Any]:
    return cast(
        "dict[str, Any]",
        yaml.safe_load((ROOT / "configs" / "default.yaml").read_text(encoding="utf-8")),
    )


def _field_default(model: type[BaseModel], name: str) -> Any:
    return model.model_fields[name].default


def test_project_version_is_consistent() -> None:
    config = _config()
    assert config["project"]["version"] == __version__
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == __version__


def test_literature_defaults_match() -> None:
    expected = _config()["literature"]
    for name in (
        "request_timeout_seconds",
        "openalex_min_interval_seconds",
        "semantic_scholar_min_interval_seconds",
        "arxiv_min_interval_seconds",
        "fulltext_min_interval_seconds",
    ):
        assert _field_default(LiteratureSettings, name) == expected[name], name


def test_retrieval_defaults_match() -> None:
    expected = _config()["retrieval"]
    assert (
        inspect.signature(HybridRetriever.__init__).parameters["rrf_k"].default
        == (expected["rrf_k"])
    )


def test_phase4_defaults_match() -> None:
    expected = _config()["phase4"]
    for name in (
        "min_entity_support",
        "min_contradiction_support",
        "min_condition_support",
        "min_limitation_support",
        "min_graph_degree",
        "min_common_neighbors",
        "max_underexplored_coverage",
        "max_candidates_per_type",
    ):
        assert _field_default(GapDiscoveryConfig, name) == expected[name], name


def test_phase5_defaults_match() -> None:
    expected = _config()["phase5"]
    for name in (
        "external_results_per_query",
        "local_results_per_query",
        "max_queries_per_gap",
        "min_direct_similarity",
        "near_match_similarity",
        "min_broad_searches",
        "include_local",
        "include_external",
        "allow_status_transition",
        "deep_verify",
        "max_deep_verifications",
        "require_deep_verification_for_supported",
        "deep_verification_similarity_floor",
    ):
        assert _field_default(NoveltyVerificationConfig, name) == expected[name], name
    assert expected["temporal_cutoff"] is None


def test_phase6_defaults_match() -> None:
    expected = _config()["phase6"]
    for name in (
        "hypotheses_per_gap",
        "max_composed_pairs",
        "dedup_similarity_threshold",
        "tournament_size",
        "tournament_rounds",
        "pareto_limit",
        "keep_diverse_limit",
        "evolve_top_k",
        "max_evolution_generations",
        "clustering_threshold",
    ):
        assert _field_default(HypothesisConfig, name) == expected[name], name
    assert _field_default(HypothesisConfig, "allow_uncertain_gaps") is False
    assert expected["min_gap_status"] == GapStatus.SURVIVED.value


def test_phase7_defaults_match() -> None:
    expected = _config()["phase7"]
    assert _field_default(SandboxPolicy, "network_enabled") is False
    assert _field_default(SandboxPolicy, "allow_gpu") is False
    assert _field_default(SandboxPolicy, "read_only_root") is True
    for name in ("memory_mb", "cpu_count", "timeout_seconds", "pids_limit"):
        assert _field_default(SandboxPolicy, name) == expected[name], name
    params = inspect.signature(build_experiment_spec).parameters
    assert params["image"].default == expected["default_image"]
    assert params["timeout_seconds"].default == expected["timeout_seconds"]
    assert expected["default_seeds"] == [1, 2, 3]


def test_phase8_defaults_match() -> None:
    expected = _config()["phase8"]
    assert inspect.signature(evaluate_retrieval).parameters["k"].default == expected["retrieval_k"]
    params = inspect.signature(bootstrap_mean_ci).parameters
    assert params["samples"].default == expected["bootstrap_samples"]
    assert params["alpha"].default == expected["bootstrap_alpha"]
    assert (
        inspect.signature(compare_baselines).parameters["direction"].default
        == expected["baseline_metric_direction"]
    )


def test_phase9_defaults_match() -> None:
    expected = _config()["phase9"]
    for name in (
        "max_iterations",
        "max_stage_retries",
        "checkpoint_every_stage",
        "stop_on_critical_review",
        "stop_on_no_progress",
        "no_progress_patience",
        "require_phase8_evaluation",
        "require_review_before_next_iteration",
    ):
        assert _field_default(AutonomousRunConfig, name) == expected[name], name
