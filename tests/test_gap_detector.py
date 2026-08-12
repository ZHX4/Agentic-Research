from pathlib import Path

from agentic_research.gaps import detect_missing_combinations
from agentic_research.ingestion.jsonl import load_papers


def test_demo_contains_unobserved_combinations() -> None:
    path = Path("data/demo/papers.jsonl")
    papers = list(load_papers(path))
    gaps = detect_missing_combinations(papers)
    pairs = {(gap.method, gap.dataset) for gap in gaps}
    assert ("Retriever-A", "Dataset-Beta") in pairs
    assert ("Retriever-B", "Dataset-Alpha") not in pairs


def test_gap_detector_never_claims_verified_novelty() -> None:
    papers = [
        {
            "paper_id": "p1",
            "title": "A",
            "methods": ["M1"],
            "tasks": ["T"],
            "datasets": ["D1"],
        },
        {
            "paper_id": "p2",
            "title": "B",
            "methods": ["M2"],
            "tasks": ["T"],
            "datasets": ["D2"],
        },
    ]
    from agentic_research.schemas import Paper

    gaps = detect_missing_combinations([Paper.model_validate(p) for p in papers])
    assert gaps
    assert all(gap.status.value == "candidate" for gap in gaps)
