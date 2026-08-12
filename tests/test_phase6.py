import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentic_research.hypotheses import run_hypothesis_reasoning
from agentic_research.hypotheses.cli import app
from agentic_research.hypotheses.diversity import cluster_hypotheses
from agentic_research.schemas.gap import GapCandidate, GapStatus
from agentic_research.schemas.phase6 import HypothesisConfig
from agentic_research.schemas.phase5 import GapVerificationResult, NoveltyVerificationReport


def make_gap(gap_id: str = "g1", status: GapStatus = GapStatus.SURVIVED) -> GapCandidate:
    return GapCandidate(gap_id=gap_id, gap_type="missing_combination", statement="missing", method="M", dataset="D", task="T", evidence_paper_ids=["p1"], signal_ids=["s1"], support_count=3, structural_support=0.7, confidence=0.8, status=status, rationale="verified")


def test_disproved_gaps_are_excluded() -> None:
    run = run_hypothesis_reasoning([make_gap("good"), make_gap("bad", GapStatus.DISPROVED)])
    assert not any("bad" in item.hypothesis.source_gap_ids for item in run.candidates)


def test_run_is_deterministic() -> None:
    cfg = HypothesisConfig(max_evolution_generations=1)
    a = run_hypothesis_reasoning([make_gap("a"), make_gap("b")], cfg)
    b = run_hypothesis_reasoning([make_gap("b"), make_gap("a")], cfg)
    assert a.run_id == b.run_id
    assert a.selected_hypothesis_ids == b.selected_hypothesis_ids


def test_reflection_and_falsification_exist() -> None:
    run = run_hypothesis_reasoning([make_gap()])
    assert run.candidates
    assert all(item.hypothesis.falsification_condition for item in run.candidates)
    assert all(item.reflection.falsification_condition for item in run.candidates)


def test_evolution_artifacts_are_integrity_safe() -> None:
    run = run_hypothesis_reasoning([make_gap()], HypothesisConfig(max_evolution_generations=2))
    assert run.evolved_count > 0
    assert run.initial_generated_count + run.evolved_count == run.generated_count
    ids = {item.hypothesis.hypothesis_id for item in run.candidates}
    assert set(run.selected_hypothesis_ids) <= ids
    assert set(run.pareto_frontier_ids) <= set(run.selected_hypothesis_ids)


def test_clustering_is_deterministic() -> None:
    run = run_hypothesis_reasoning([make_gap("a"), make_gap("b")])
    first = cluster_hypotheses(run.candidates)
    second = cluster_hypotheses(run.candidates)
    assert [[x.hypothesis.hypothesis_id for x in c] for c in first] == [[x.hypothesis.hypothesis_id for x in c] for c in second]
    assert len(first) == run.cluster_count


def test_invalid_config_rejected() -> None:
    with pytest.raises(ValueError):
        HypothesisConfig(evolve_top_k=10, keep_diverse_limit=5)


def test_cli_writes_artifact(tmp_path: Path) -> None:
    inp = tmp_path / "phase5.json"
    out = tmp_path / "phase6.json"
    verification = GapVerificationResult(verification_id="v1", gap_id="g1", original_status=GapStatus.CANDIDATE, resulting_status=GapStatus.SURVIVED, verdict="supported", coverage="broad", confidence=0.7, rationale="survived", verified_candidate=make_gap())
    inp.write_text(NoveltyVerificationReport(run_id="r", input_candidate_count=1, results=[verification]).model_dump_json(), encoding="utf-8")
    result = CliRunner().invoke(app, ["reason", "--input", str(inp), "--output", str(out), "--max-evolution-generations", "0"])
    assert result.exit_code == 0
    assert out.exists()
    json.loads(out.read_text(encoding="utf-8"))
