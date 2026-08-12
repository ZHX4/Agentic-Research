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


def test_gap_is_candidate_by_default() -> None:
    gap = GapCandidate(
        gap_id="g1",
        gap_type="missing_combination",
        statement="candidate",
        confidence=0.3,
        rationale="observed absence",
    )
    assert gap.status == GapStatus.CANDIDATE
