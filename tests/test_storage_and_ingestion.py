from pathlib import Path

import pytest

from agentic_research.ingestion.jsonl import load_papers
from agentic_research.schemas import Paper
from agentic_research.storage.jsonl import JsonlStore


def test_jsonl_loader_reports_bad_rows(tmp_path: Path) -> None:
    path = tmp_path / "papers.jsonl"
    path.write_text(
        '{"paper_id":"p1","title":"Good"}\n'
        '{"paper_id":"p2","title":"Good"}\n'
        '{"paper_id":"","title":"Bad"}\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=r"papers\.jsonl:3"):
        list(load_papers(path))


def test_jsonl_store_round_trip(tmp_path: Path) -> None:
    store = JsonlStore(tmp_path / "papers.jsonl")
    paper = Paper(paper_id="p1", title="Example", methods=["M"])

    store.append(paper)

    restored = store.read(Paper)
    assert restored == [paper]


def test_jsonl_store_missing_file_is_empty(tmp_path: Path) -> None:
    store = JsonlStore(tmp_path / "missing.jsonl")
    assert store.read(Paper) == []
