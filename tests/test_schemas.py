import pytest
from pydantic import ValidationError

from agentic_research.schemas import GapCandidate, GapStatus, Paper


def test_paper_validation() -> None:
    paper = Paper(
        paper_id="p1",
        title="Example",
        methods=["M"],
        tasks=["T"],
        datasets=["D"],
    )
    assert paper.paper_id == "p1"


def test_paper_rejects_blank_identity_fields() -> None:
    with pytest.raises(ValidationError):
        Paper(paper_id="", title="Example")

    with pytest.raises(ValidationError):
        Paper(paper_id="p1", title="")


def test_paper_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Paper.model_validate({"paper_id": "p1", "title": "Example", "unexpected": True})


def test_gap_is_candidate_by_default() -> None:
    gap = GapCandidate(
        gap_id="g1",
        gap_type="missing_combination",
        statement="candidate",
        confidence=0.3,
        rationale="observed absence",
    )
    assert gap.status == GapStatus.CANDIDATE


def test_gap_status_is_not_implicitly_verified() -> None:
    gap = GapCandidate(
        gap_id="g1",
        gap_type="missing_combination",
        statement="candidate",
        confidence=0.9,
        rationale="observed absence",
    )
    assert gap.status == GapStatus.CANDIDATE
