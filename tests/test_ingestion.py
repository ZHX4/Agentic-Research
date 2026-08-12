from pathlib import Path

import pytest

from agentic_research.ingestion.jsonl import load_papers


def test_jsonl_loader_reads_valid_papers(tmp_path: Path) -> None:
    path = tmp_path / "papers.jsonl"
    path.write_text(
        '{"paper_id":"p1","title":"Example","tasks":["T"]}\n',
        encoding="utf-8",
    )

    papers = list(load_papers(path))

    assert len(papers) == 1
    assert papers[0].paper_id == "p1"


def test_jsonl_loader_reports_bad_rows(tmp_path: Path) -> None:
    path = tmp_path / "papers.jsonl"
    path.write_text('{"paper_id":"p1"}\n', encoding="utf-8")

    with pytest.raises(ValueError, match=r"Invalid paper at .+:1:"):
        list(load_papers(path))
