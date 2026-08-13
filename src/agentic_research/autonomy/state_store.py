"""Durable SQLite persistence for resumable autonomous research runs."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from agentic_research.schemas.phase9 import AutonomousRunState, Checkpoint


class SQLiteRunStore:
    """Persist complete run state atomically and support checkpoint/resume."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, state_json TEXT NOT NULL, state_sha256 TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS checkpoints (checkpoint_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, checkpoint_json TEXT NOT NULL, FOREIGN KEY(run_id) REFERENCES runs(run_id))"
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def save(self, state: AutonomousRunState, state_sha256: str) -> None:
        payload = state.model_dump_json()
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO runs(run_id, state_json, state_sha256) VALUES (?, ?, ?) "
                "ON CONFLICT(run_id) DO UPDATE SET state_json=excluded.state_json, state_sha256=excluded.state_sha256",
                (state.run_id, payload, state_sha256),
            )
            connection.commit()

    def load(self, run_id: str) -> tuple[AutonomousRunState, str] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT state_json, state_sha256 FROM runs WHERE run_id=?", (run_id,)
            ).fetchone()
        if row is None:
            return None
        state = AutonomousRunState.model_validate_json(row[0])
        return state, str(row[1])

    def save_checkpoint(self, checkpoint: Checkpoint, state: AutonomousRunState, state_sha256: str) -> None:
        self.save(state, state_sha256)
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO checkpoints(checkpoint_id, run_id, checkpoint_json) VALUES (?, ?, ?)",
                (checkpoint.checkpoint_id, checkpoint.run_id, checkpoint.model_dump_json()),
            )
            connection.commit()

    def latest_checkpoint(self, run_id: str) -> Checkpoint | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT checkpoint_json FROM checkpoints WHERE run_id=? ORDER BY rowid DESC LIMIT 1",
                (run_id,),
            ).fetchone()
        return None if row is None else Checkpoint.model_validate_json(row[0])

    def list_run_ids(self) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute("SELECT run_id FROM runs ORDER BY rowid").fetchall()
        return [str(row[0]) for row in rows]
