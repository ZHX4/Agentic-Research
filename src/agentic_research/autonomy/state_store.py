from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from agentic_research.schemas.phase9 import AutonomousRunState, Checkpoint


class SQLiteRunStore:
    """Durable state and atomic checkpoint snapshots for Phase 9."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, state_json TEXT NOT NULL, state_sha256 TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS checkpoints (checkpoint_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, checkpoint_json TEXT NOT NULL, state_snapshot_json TEXT NOT NULL, FOREIGN KEY(run_id) REFERENCES runs(run_id))")
            db.commit()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.execute("PRAGMA foreign_keys=ON")
        return db

    @staticmethod
    def state_hash(state: AutonomousRunState) -> str:
        return hashlib.sha256(state.model_dump_json().encode()).hexdigest()

    @staticmethod
    def checkpoint_hash(state: AutonomousRunState) -> str:
        last = state.checkpoints[-1]
        normalized = last.model_copy(update={"state_sha256": "0" * 64})
        clone = state.model_copy(update={"checkpoints": [*state.checkpoints[:-1], normalized]})
        return SQLiteRunStore.state_hash(clone)

    def save(self, state: AutonomousRunState, state_sha256: str) -> None:
        with self._connect() as db:
            db.execute("INSERT INTO runs VALUES (?, ?, ?) ON CONFLICT(run_id) DO UPDATE SET state_json=excluded.state_json, state_sha256=excluded.state_sha256", (state.run_id, state.model_dump_json(), state_sha256))
            db.commit()

    def save_checkpoint(self, checkpoint: Checkpoint, state: AutonomousRunState, state_sha256: str) -> None:
        snapshot = state.model_dump_json()
        with self._connect() as db:
            db.execute("INSERT INTO runs VALUES (?, ?, ?) ON CONFLICT(run_id) DO UPDATE SET state_json=excluded.state_json, state_sha256=excluded.state_sha256", (state.run_id, snapshot, state_sha256))
            db.execute("INSERT OR REPLACE INTO checkpoints VALUES (?, ?, ?, ?)", (checkpoint.checkpoint_id, checkpoint.run_id, checkpoint.model_dump_json(), snapshot))
            db.commit()

    def load(self, run_id: str) -> tuple[AutonomousRunState, str] | None:
        with self._connect() as db:
            row = db.execute("SELECT state_json, state_sha256 FROM runs WHERE run_id=?", (run_id,)).fetchone()
            cp = db.execute("SELECT checkpoint_json, state_snapshot_json FROM checkpoints WHERE run_id=? ORDER BY rowid DESC LIMIT 1", (run_id,)).fetchone()
        if row is None:
            return None
        state = AutonomousRunState.model_validate_json(row[0])
        if self.state_hash(state) != row[1]:
            raise ValueError("Persisted state hash mismatch")
        if cp:
            checkpoint = Checkpoint.model_validate_json(cp[0])
            snapshot = AutonomousRunState.model_validate_json(cp[1])
            if checkpoint.checkpoint_id != snapshot.checkpoints[-1].checkpoint_id or self.checkpoint_hash(snapshot) != checkpoint.state_sha256:
                raise ValueError("Checkpoint snapshot integrity mismatch")
        return state, str(row[1])

    def latest_checkpoint(self, run_id: str) -> Checkpoint | None:
        with self._connect() as db:
            row = db.execute("SELECT checkpoint_json, state_snapshot_json FROM checkpoints WHERE run_id=? ORDER BY rowid DESC LIMIT 1", (run_id,)).fetchone()
        if row is None:
            return None
        checkpoint = Checkpoint.model_validate_json(row[0])
        snapshot = AutonomousRunState.model_validate_json(row[1])
        if self.checkpoint_hash(snapshot) != checkpoint.state_sha256:
            raise ValueError("Checkpoint snapshot integrity mismatch")
        return checkpoint

    def list_run_ids(self) -> list[str]:
        with self._connect() as db:
            return [str(row[0]) for row in db.execute("SELECT run_id FROM runs ORDER BY rowid").fetchall()]
