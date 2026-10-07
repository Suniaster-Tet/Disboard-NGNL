#!/usr/bin/env python3
"""Local token-usage counters; prompt and completion contents are never stored."""
import os
import sqlite3
import time
from pathlib import Path


DATA_DIR = Path(os.environ.get("DISBOARD_DATA_DIR", ".disboard-local")).expanduser()


def estimate_tokens(text):
    return max(1, (len(text) + 3) // 4) if text else 0


class UsageLedger:
    def __init__(self, database_path=None):
        data_dir = Path(os.environ.get("DISBOARD_DATA_DIR", DATA_DIR)).expanduser()
        data_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            data_dir.chmod(0o700)
        except OSError:
            pass
        self.database_path = Path(database_path or data_dir / "usage.sqlite3")
        descriptor = os.open(self.database_path, os.O_CREAT | os.O_RDWR, 0o600)
        os.close(descriptor)
        try:
            self.database_path.chmod(0o600)
        except OSError:
            pass
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS usage_events (
                    id INTEGER PRIMARY KEY,
                    occurred_at INTEGER NOT NULL,
                    agent TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    token_source TEXT NOT NULL
                )"""
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS usage_time_agent ON usage_events(occurred_at, agent)"
            )

    def _connect(self):
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def record(self, agent, provider, model, input_tokens, output_tokens, token_source):
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO usage_events
                (occurred_at, agent, provider, model, input_tokens, output_tokens, token_source)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    int(time.time()), agent, provider, model,
                    max(0, int(input_tokens)), max(0, int(output_tokens)), token_source,
                ),
            )

    def summary(self, agent="", hours=24):
        since = int(time.time()) - int(hours * 3600)
        query = """SELECT agent, provider, model,
            SUM(input_tokens) AS input_tokens,
            SUM(output_tokens) AS output_tokens,
            COUNT(*) AS requests,
            SUM(CASE WHEN token_source = 'reported' THEN 1 ELSE 0 END) AS reported_requests,
            SUM(CASE WHEN token_source = 'estimated' THEN 1 ELSE 0 END) AS estimated_requests
            FROM usage_events WHERE occurred_at >= ?"""
        parameters = [since]
        if agent:
            query += " AND lower(agent) = lower(?)"
            parameters.append(agent)
        query += " GROUP BY agent, provider, model ORDER BY agent, provider, model"
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [dict(row) for row in rows]