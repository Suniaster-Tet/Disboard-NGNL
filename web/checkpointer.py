"""Checkpointer SQLite persistente para el grafo web."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


class WebCheckpointer(SqliteSaver):
    """Saver oficial de LangGraph respaldado por la base SQLite local."""

    def __init__(self, db_path: str | Path | None = None):
        path = Path(
            db_path
            or os.getenv("DISBOARD_WEB_CHECKPOINT_DB", "logs/web_graph_checkpoints.sqlite")
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(sqlite3.connect(path, check_same_thread=False))
        self.setup()
