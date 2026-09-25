"""PEFT-30 benchmark infrastructure tests (DEV fixtures only).

Every fixture here is synthetic and explicitly NOT sci-bench-peft30-v1.
These tests pin the measuring instrument: manifest hashing, freeze
refusal, annotation-trail preservation, temporal splits, sweep
determinism, provenance math, and snapshot hashing.
"""

from __future__ import annotations

import pytest

from agentic_research.benchmarks.annotations import (
    SingleAnnotation,
    build_adjudicated,
)
from agentic_research.benchmarks.hypothesis_dims import HypothesisDimensionRating
from agentic_research.benchmarks.manifest import (
    PaperRecord,
    build_draft_manifest,
    compute_corpus_sha256,
    freeze_manifest,
    temporal_split,
    validate_manifest,
)
from agentic_research.benchmarks.provenance import (
    ProvenanceJoinInput,
    build_provenance_report,
)
from agentic_research.benchmarks.runner import (
    gap_cases_from_adjudicated,
    human_ratings_from_adjudicated,
    run_agreement,
    run_gap_evaluation,
    run_temporal_evaluation,
)
from agentic_research.benchmarks.snapshots import build_snapshot, validate_snapshot
from agentic_research.benchmarks.sweep import (
    SENSITIVITY_NOTE,
    build_sweep_report,
    sweep_configurations,
    sweep_report_id,
)
from agentic_research.schemas.phase8 import PredictionRecord


def dev_paper(paper_id: str, year: int | None, status: str = "metadata-only") -> PaperRecord:
    payload = {
        "paper_id": paper_id,
        "title": f"DEV {paper_id} (synthetic, not PEFT-30-v1)",
        "year": year,
        "source": "dev",
        "fulltext_status": status,
    }
    if status in ("pdf", "html"):
        payload["local_path"] = f"{paper_id}.pdf"
    record = PaperRecord.model_validate(payload)
    return record


def dev_annotation(case_id: str, annotator: str, label: str) -> SingleAnnotation:
    return SingleAnnotation(
        case_id=case_id,
        annotator_id=annotator,
        label=label,
        evidence_refs=["dev:section:1"],
        quoted_passages=["dev passage"],
        rationale="dev rationale",
        source_paper_ids=["dev-001"],
        temporal_context="pre-cutoff-2022",
        confidence=0.6,
    )


def test_manifest_hash_is_deterministic() -> None:
    papers = [dev_paper("dev-001", 2021), dev_paper("dev-002", 2023)]
    first = compute_corpus_sha256(papers)
    second = compute_corpus_sha256(list(reversed(papers)))
    assert first == second
    assert len(first) == 64


def test_manifest_validation_detects_hash_mismatch() -> None:
    manifest = build_draft_manifest(
        [dev_paper("dev-001", 2021)],
        collection_method="dev",
        sources=["dev"],
        collection_date_utc="2026-01-01T00:00:00+00:00",
    )
    assert validate_manifest(manifest) == []
    tampered = manifest.model_copy(update={"corpus_sha256": "0" * 64})
    problems = validate_manifest(tampered)
    assert any("corpus_sha256" in problem for problem in problems)


def test_freeze_refuses_mutation(tmp_path: object) -> None:
    from pathlib import Path

    root = Path(str(tmp_path))
    manifest = build_draft_manifest(
        [dev_paper("dev-001", 2021)],
        collection_method="dev",
        sources=["dev"],
        collection_date_utc="2026-01-01T00:00:00+00:00",
    )
    output = root / "manifest.json"
    freeze_manifest(manifest, output)
    assert output.is_file()
    # Idempotent rewrite with identical content is allowed.
    freeze_manifest(manifest, output)
    other = build_draft_manifest(
        [dev_paper("dev-001", 2021), dev_paper("dev-002", 2021)],
        collection_method="dev",
        sources=["dev"],
        collection_date_utc="2026-01-01T00:00:00+00:00",
    )
    with pytest.raises(ValueError, match="Refusing to overwrite"):
        freeze_manifest(other, output)


def test_double_annotation_requires_distinct_annotators() -> None:
    first = dev_annotation("case-001", "annotator-a", "valid_opportunity")
    second = dev_annotation("case-001", "annotator-a", "valid_opportunity")
    with pytest.raises(ValueError, match="distinct annotators"):
        build_adjudicated(
            first,
            second,
            kind="gap",
            adjudicator_id="judge-1",
            adjudicated_label="valid_opportunity",
        )


def test_disagreement_and_adjudication_preserved() -> None:
    first = dev_annotation("case-001", "annotator-a", "valid_opportunity")
    second = dev_annotation("case-001", "annotator-b", "partially_addressed")
    record = build_adjudicated(
        first,
        second,
        kind="gap",
        adjudicator_id="judge-1",
        adjudicated_label="partially_addressed",
        dissent_note="B saw adjacent work.",
    )
    assert record.disagreement is True
    assert record.annotation_a.label == "valid_opportunity"
    assert record.annotation_b.label == "partially_addressed"
    assert record.final_label == "partially_addressed"
    assert record.dissent_note == "B saw adjacent work."


def test_invalid_label_rejected() -> None:
    first = dev_annotation("case-001", "annotator-a", "made-up-label")
    second = dev_annotation("case-001", "annotator-b", "valid_opportunity")
    with pytest.raises(ValueError, match="not allowed"):
        build_adjudicated(
            first,
            second,
            kind="gap",
            adjudicator_id="judge-1",
            adjudicated_label="valid_opportunity",
        )


def test_temporal_split_correctness() -> None:
    manifest = build_draft_manifest(
        [
            dev_paper("pre-001", 2021),
            dev_paper("pre-002", 2022),
            dev_paper("post-001", 2023),
            dev_paper("unk-001", None),
        ],
        collection_method="dev",
        sources=["dev"],
        collection_date_utc="2026-01-01T00:00:00+00:00",
    )
    split = temporal_split(manifest)
    assert split["discovery"] == ["pre-001", "pre-002"]
    assert split["post_cutoff_probes"] == ["post-001"]
    assert split["unknown_year"] == ["unk-001"]
    # Post-cutoff must never enter the historical discovery set.
    assert "post-001" not in split["discovery"]


def test_gap_case_integrity_and_evaluation() -> None:
    records = [
        build_adjudicated(
            dev_annotation("gap-001", "annotator-a", "valid_opportunity"),
            dev_annotation("gap-001", "annotator-b", "valid_opportunity"),
            kind="gap",
            adjudicator_id="judge-1",
            adjudicated_label="valid_opportunity",
        )
    ]
    cases = gap_cases_from_adjudicated(records)
    assert len(cases) == 1
    assert cases[0].expected_labels == ["valid_opportunity"]
    result = run_gap_evaluation(
        records,
        [PredictionRecord(case_id="gap-001", predicted_labels=["valid_opportunity"])],
        system_name="dev-system",
    )
    assert result.cases_evaluated == 1


def test_temporal_evaluation_requires_cutoff() -> None:
    result = run_temporal_evaluation(
        ["case-t1"],
        [PredictionRecord(case_id="case-t1", publication_years={"p1": 2021})],
        system_name="dev-system",
    )
    assert result.kind == "temporal"


def test_agreement_uses_existing_phase8_machinery() -> None:
    records = [
        build_adjudicated(
            dev_annotation("gap-001", "annotator-a", "valid_opportunity"),
            dev_annotation("gap-001", "annotator-b", "valid_opportunity"),
            kind="gap",
            adjudicator_id="judge-1",
            adjudicated_label="valid_opportunity",
        ),
        build_adjudicated(
            dev_annotation("gap-002", "annotator-a", "unsupported"),
            dev_annotation("gap-002", "annotator-b", "unsupported"),
            kind="gap",
            adjudicator_id="judge-1",
            adjudicated_label="unsupported",
        ),
    ]
    ratings = human_ratings_from_adjudicated(records)
    assert len(ratings) == 4
    outcome = run_agreement(records, task="gap_quality")
    assert outcome.item_count == 2
    assert outcome.annotator_count == 2


def test_sweep_is_deterministic_and_report_only() -> None:
    first = sweep_configurations()
    second = sweep_configurations()
    assert first == second
    assert any(cfg["near_match_similarity"] == 0.62 for cfg in first)
    assert any(cfg["min_entity_support"] == 3 for cfg in first)
    assert "prohibited" in SENSITIVITY_NOTE
    report = build_sweep_report("sci-bench-peft30-v1", [])
    assert "prohibited" in report.note
    assert report.report_id == sweep_report_id("sci-bench-peft30-v1", [dict(report.baseline)])


def test_provenance_join_reports_phase6_loss() -> None:
    report = build_provenance_report(
        ProvenanceJoinInput(
            gap_count=4,
            gaps_with_source_papers=4,
            gaps_with_passages=2,
            verdict_count=4,
            verdicts_with_evidence=3,
            hypothesis_count=4,
            hypotheses_with_gap_link=4,
            hypotheses_with_direct_paper_link=0,
        )
    )
    assert report.gaps_with_source_papers_pct == 100.0
    assert report.gaps_with_passages_pct == 50.0
    assert report.verdicts_with_evidence_pct == 75.0
    assert report.hypotheses_with_gap_link_pct == 100.0
    assert report.hypotheses_with_direct_paper_link_pct == 0.0
    assert "source_gap_ids" in report.known_loss


def test_provider_snapshot_determinism() -> None:
    first = build_snapshot(
        provider="arxiv",
        query="LoRA fine-tuning",
        collected_at_utc="2026-01-01T00:00:00+00:00",
        result_ids=["a", "b"],
        temporal_filter="year<=2022",
    )
    second = build_snapshot(
        provider="arxiv",
        query="LoRA fine-tuning",
        collected_at_utc="2026-06-01T00:00:00+00:00",
        result_ids=["b", "a"],
        temporal_filter="year<=2022",
    )
    assert first.payload_hash == second.payload_hash
    assert validate_snapshot(first) == []


def test_hypothesis_dimensions_have_no_total_score() -> None:
    rating = HypothesisDimensionRating(
        hypothesis_id="h-001",
        annotator_id="annotator-a",
        research_question_distinct=True,
        intervention_distinct=True,
        rationale="dev",
        textual_vs_scientific_note="Same wording, different intervention.",
    )
    assert rating.distinct_count() == 2
    assert not hasattr(rating, "overall_score")
