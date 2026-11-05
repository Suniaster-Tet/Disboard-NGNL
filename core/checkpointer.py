"""Checkpointer compartido consola/web.

- Por defecto: SQLite local en `logs/disboard_checkpoints.db`.
- Si `CHECKPOINTER_BACKEND=postgres`: usa `langgraph-checkpoint-postgres`.
- Traza estructurada en `logs/graph_trace.jsonl`.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class DisboardCheckpointer:
    def __init__(
        self,
        db_path: str
