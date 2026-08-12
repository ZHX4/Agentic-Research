"""Small, dependency-light JSONL persistence used by the MVP.

The interface is intentionally replaceable by PostgreSQL/pgvector later.
"""

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class JsonlStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, item: BaseModel) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(item.model_dump(mode="json"), ensure_ascii=False) + "\n")

    def read(self, model: type[T]) -> list[T]:
        if not self.path.exists():
            return []
        records: list[T] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    records.append(model.model_validate_json(line))
        return records
