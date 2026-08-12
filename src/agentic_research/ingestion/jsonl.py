"""Local JSONL corpus loader for the deterministic MVP."""

import json
from pathlib import Path
from typing import Iterator

from agentic_research.schemas import Paper


def load_papers(path: Path) -> Iterator[Paper]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            raw = line.strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
                yield Paper.model_validate(payload)
            except Exception as exc:  # validation errors should identify the bad row
                raise ValueError(f"Invalid paper at {path}:{line_number}: {exc}") from exc
