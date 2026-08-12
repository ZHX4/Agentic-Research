from pathlib import Path

from agentic_research.schemas import Paper
from agentic_research.storage.jsonl import JsonlStore


def test_jsonl_store_round_trip(tmp_path: Path) -> None:
    store = JsonlStore(tmp_path / "papers.jsonl")
    paper = Paper(
        paper_id="p1",
        title="Example",
        methods=["M"],
        tasks=["T"],
        datasets=["D"],
    )

    store.append(paper)
    records = store.read(Paper)

    assert records == [paper]


def test_jsonl_store_missing_file_is_empty(tmp_path: Path) -> None:
    store = JsonlStore(tmp_path / "missing.jsonl")
    assert store.read(Paper) == []
