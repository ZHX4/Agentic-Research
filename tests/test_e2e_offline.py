"""Offline end-to-end release regression test.

Mirrors ``scripts/e2e_offline.sh`` through the real CLI boundaries
(single-command apps invoked without a subcommand prefix, group apps with
their subcommand) using only offline backends: hash embeddings, local
world-model search, no deep full-text verification, and the autonomous
control-plane smoke path. Docker execution is intentionally not exercised.

Proves the shipped workflow completes and that publication readiness is
evidence-gated end to end — not just per-phase in isolation.
"""

from __future__ import annotations

import json
from pathlib import Path

import fitz
from typer import Typer
from typer.testing import CliRunner

from agentic_research.autonomy.cli import app as autonomy_app
from agentic_research.cli import app as main_app
from agentic_research.evaluation.cli import app as evaluation_app
from agentic_research.execution.cli import app as execution_app
from agentic_research.hypotheses.cli import app as hypotheses_app
from agentic_research.publication.cli import app as publication_app
from agentic_research.verification.cli import app as verification_app

runner = CliRunner()


def _paper(pid: str, title: str, method: str, dataset: str) -> dict[str, object]:
    return {
        "paper_id": pid,
        "title": title,
        "year": 2024,
        "authors": ["E2E Author"],
        "methods": [method],
        "tasks": ["e2e-task"],
        "datasets": [dataset],
    }


def _write_pdf(path: Path, title: str) -> None:
    document = fitz.open()
    page = document.new_page(width=600, height=800)
    page.insert_text((60, 60), title, fontsize=18)
    page.insert_text((60, 100), "Introduction", fontsize=16)
    page.insert_text((60, 130), "Retrieval systems can improve factual accuracy [1].")
    page.insert_text((60, 160), "Methods", fontsize=16)
    page.insert_text((60, 190), "We propose a retrieval method and evaluate it.")
    page.insert_text((60, 220), "Results", fontsize=16)
    page.insert_text((60, 250), "Our method improves accuracy over the baseline.")
    page.insert_text((60, 280), "References", fontsize=16)
    page.insert_text((60, 310), "[1] Alice Example. Retrieval Systems. 2024. doi:10.1234/XYZ")
    document.save(path)
    document.close()


def _invoke(args: list[str], app: Typer) -> None:
    result = runner.invoke(app, args)
    assert result.exit_code == 0, f"{args} failed: {result.output}"


def test_offline_release_chain(tmp_path: Path) -> None:
    papers = [
        _paper("e2e-001", "E2E Study A", "E2E-Method-Alpha", "E2E-Data-Alpha"),
        _paper("e2e-002", "E2E Study B", "E2E-Method-Beta", "E2E-Data-Beta"),
    ]
    corpus = tmp_path / "corpus.jsonl"
    with corpus.open("w", encoding="utf-8") as handle:
        for paper in papers:
            handle.write(json.dumps(paper) + "\n")
            (tmp_path / f"{paper['paper_id']}.json").write_text(json.dumps(paper), encoding="utf-8")
            _write_pdf(tmp_path / f"{paper['paper_id']}.pdf", str(paper["title"]))

    _invoke(["demo"], main_app)
    _invoke(["validate", "--input", str(corpus)], main_app)
    gaps = tmp_path / "gaps.json"
    _invoke(["gaps", "--input", str(corpus), "--output", str(gaps)], main_app)
    assert json.loads(gaps.read_text(encoding="utf-8"))

    analyses = []
    for paper in papers:
        out = tmp_path / f"analysis-{paper['paper_id']}.json"
        _invoke(
            [
                "analyze",
                "--paper",
                str(tmp_path / f"{paper['paper_id']}.json"),
                "--pdf",
                str(tmp_path / f"{paper['paper_id']}.pdf"),
                "--output",
                str(out),
            ],
            main_app,
        )
        analyses.append(out)

    world = tmp_path / "world.sqlite"
    for analysis in analyses:
        _invoke(
            [
                "index",
                "--input",
                str(analysis),
                "--database",
                str(world),
                "--embedding",
                "hash",
            ],
            main_app,
        )
    assert world.is_file()

    _invoke(
        [
            "retrieve",
            "retrieval accuracy",
            "--database",
            str(world),
            "--limit",
            "5",
            "--mode",
            "hybrid",
            "--embedding",
            "hash",
            "--reranker",
            "lexical",
        ],
        main_app,
    )
    _invoke(
        ["traverse", "paper:e2e-001", "--database", str(world), "--depth", "1"],
        main_app,
    )

    gaps4 = tmp_path / "gaps4.json"
    _invoke(
        [
            "discover-gaps",
            "--database",
            str(world),
            "--output",
            str(gaps4),
            "--min-entity-support",
            "1",
            "--include-type",
            "missing_combination",
        ],
        main_app,
    )
    discovery = json.loads(gaps4.read_text(encoding="utf-8"))
    assert discovery["candidates"], "discovery must yield candidates for reasoning"

    novelty = tmp_path / "novelty.json"
    # Single-command app: no subcommand prefix. Local-only, conservative,
    # no full-text downloads: verdicts stay weakened/inconclusive, never
    # fabricated novelty.
    _invoke(
        [
            "--input",
            str(gaps4),
            "--output",
            str(novelty),
            "--database",
            str(world),
            "--no-external",
            "--no-deep-verify",
        ],
        verification_app,
    )
    report = json.loads(novelty.read_text(encoding="utf-8"))
    assert report["results"]
    assert all(
        item["verdict"] in {"weakened", "inconclusive", "supported"} for item in report["results"]
    )
    for item in report["results"]:
        if item["verdict"] == "supported":
            assert item.get("deep_evidence"), "supported requires deep evidence"

    hyp = tmp_path / "hyp.json"
    _invoke(
        [
            "--input",
            str(novelty),
            "--output",
            str(hyp),
            "--max-evolution-generations",
            "0",
            "--min-gap-status",
            "uncertain",
            "--allow-uncertain-gaps",
        ],
        hypotheses_app,
    )
    run = json.loads(hyp.read_text(encoding="utf-8"))
    assert run["selected_hypothesis_ids"], "reasoning must select hypotheses"
    hypothesis_id = run["selected_hypothesis_ids"][0]
    assert all(item["hypothesis"]["falsification_condition"] for item in run["candidates"])

    code = tmp_path / "run.py"
    code.write_text("print('e2e experiment')\n", encoding="utf-8")
    spec = tmp_path / "exp.json"
    _invoke(
        [
            "plan",
            "--hypothesis-run",
            str(hyp),
            "--hypothesis-id",
            hypothesis_id,
            "--code",
            str(code),
            "--command",
            "python",
            "--command",
            "run.py",
            "--primary-metric",
            "accuracy",
            "--metric-direction",
            "higher",
            "--output",
            str(spec),
        ],
        execution_app,
    )
    assert json.loads(spec.read_text(encoding="utf-8"))["hypothesis_id"] == hypothesis_id

    cases = tmp_path / "cases.json"
    cases.write_text(
        json.dumps(
            [
                {
                    "case_id": "c1",
                    "kind": "retrieval",
                    "input_hash": "c" * 64,
                    "expected_ids": ["a", "b"],
                }
            ]
        ),
        encoding="utf-8",
    )
    preds = tmp_path / "preds.json"
    preds.write_text(json.dumps([{"case_id": "c1", "predicted_ids": ["a", "b"]}]), encoding="utf-8")
    bench = tmp_path / "bench.json"
    _invoke(
        [
            "retrieval",
            "--cases",
            str(cases),
            "--predictions",
            str(preds),
            "--output",
            str(bench),
            "--system-name",
            "e2e",
        ],
        evaluation_app,
    )
    evaluation_report = tmp_path / "report.json"
    _invoke(
        [
            "report",
            "--system-name",
            "e2e",
            "--output",
            str(evaluation_report),
            "--benchmark",
            str(bench),
        ],
        evaluation_app,
    )
    assert json.loads(evaluation_report.read_text(encoding="utf-8"))["benchmark_results"]

    auto_in = tmp_path / "auto_in.json"
    auto_in.write_text(json.dumps({"provenance_refs": ["e2e:input"]}), encoding="utf-8")
    auto_out = tmp_path / "auto_report.json"
    _invoke(
        [
            "run",
            "--run-id",
            "e2e",
            "--state-db",
            str(tmp_path / "autonomy.sqlite"),
            "--input-file",
            str(auto_in),
            "--output",
            str(auto_out),
            "--offline-smoke-test",
            "--max-iterations",
            "1",
        ],
        autonomy_app,
    )
    assert json.loads(auto_out.read_text(encoding="utf-8"))["run_id"] == "e2e"

    artifact = tmp_path / "artifact.txt"
    artifact.write_text("hello", encoding="utf-8")
    repro = tmp_path / "repro.json"
    _invoke(
        [
            "manifest",
            "--source-commit",
            "abcdef1234567890",
            "--artifacts",
            str(spec),
            "--kinds",
            "result",
            "--licenses",
            "MIT",
            "--output",
            str(repro),
        ],
        publication_app,
    )
    arch = tmp_path / "arch.json"
    arch.write_text(json.dumps({"evidence_refs": ["e2e:arch"]}), encoding="utf-8")
    evaluation = tmp_path / "eval.json"
    evaluation.write_text(
        json.dumps({"provenance_refs": ["e2e:bench"], "benchmarks": [{"benchmark_id": "b1"}]}),
        encoding="utf-8",
    )
    case = tmp_path / "case.json"
    case.write_text(
        json.dumps(
            {
                "case_id": "e2e",
                "hypothesis": {"id": "h1"},
                "verification": {"id": "v1"},
                "execution": {"id": "e1"},
                "evaluation": {"id": "ev1"},
                "provenance_refs": ["e2e:case"],
            }
        ),
        encoding="utf-8",
    )
    disclosure = tmp_path / "disclosure.json"
    disclosure.write_text(
        json.dumps(
            [
                {
                    "provider": "e2e",
                    "model": "synthetic-smoke",
                    "role": "evaluation",
                    "local_or_remote": "local",
                    "training_data_disclosed": True,
                    "usage_notes": "Offline release-check fixtures only.",
                }
            ]
        ),
        encoding="utf-8",
    )
    bundle = tmp_path / "bundle.json"
    _invoke(
        [
            "bundle",
            "--source-commit",
            "abcdef1234567890",
            "--architecture",
            str(arch),
            "--evaluation",
            str(evaluation),
            "--case-study",
            str(case),
            "--disclosure",
            str(disclosure),
            "--reproducibility",
            str(repro),
            "--output",
            str(bundle),
        ],
        publication_app,
    )
    assert json.loads(bundle.read_text(encoding="utf-8"))["status"] == "ready"
