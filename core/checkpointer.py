"""Checkpointer compartido consola/web.

- Por defecto: SQLite local en `logs/disboard_checkpoints.db`.
- Checkpointer JSON local para usos auxiliares; el grafo web usa el saver SQLite
    oficial de LangGraph en `web/checkpointer.py`.
- Traza estructurada en `logs/graph_trace.jsonl`.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class DisboardCheckpointer:
    def __init__(
        self,
        db_path: str | Path = "logs/disboard_checkpoints.db",
        trace_path: str | Path = "logs/graph_trace.jsonl",
    ) -> None:
        self.db_path = Path(db_path)
        self.trace_path = Path(trace_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.trace_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS checkpoints (
                    thread_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )"""
            )

    def save_checkpoint(self, thread_id: str, state: Dict[str, Any]) -> None:
        serialized = json.dumps(state, ensure_ascii=False, sort_keys=True, default=str)
        timestamp = _utcnow()
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """INSERT INTO checkpoints (thread_id, state, updated_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(thread_id) DO UPDATE SET
                       state = excluded.state,
                       updated_at = excluded.updated_at""",
                (thread_id, serialized, timestamp),
            )
        self._trace("checkpoint_saved", thread_id, serialized, timestamp)

    def load_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT state FROM checkpoints WHERE thread_id = ?",
                (thread_id,),
            ).fetchone()
        if row is None:
            return None
        state = json.loads(row[0])
        return state if isinstance(state, dict) else {"state": state}

    def _trace(self, event: str, thread_id: str, serialized: str, timestamp: str) -> None:
        record = {
            "event": event,
            "thread_id": thread_id,
            "timestamp": timestamp,
            "sha256": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
        }
        with self.trace_path.open("a", encoding="utf-8") as trace:
            trace.write(json.dumps(record, ensure_ascii=False) + "\n")
