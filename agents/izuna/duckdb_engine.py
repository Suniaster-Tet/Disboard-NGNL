"""Motor DuckDB en RAM para Izuna.

Registra DataFrames procesados como tablas SQL. La construcción de la
tabla maestra de autoridades vive en `agents/izuna/authorities.py`.
"""
from __future__ import annotations

import re
from typing import Any, List, Tuple

import pandas as pd

try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:  # pragma: no cover
    duckdb = None
    HAS_DUCKDB = False


def sanitize_table_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", str(name))
    cleaned = re.sub(r"__+", "_", cleaned).strip("_").lower()
    if cleaned and cleaned[0].isdigit():
        cleaned = "_" + cleaned
    return cleaned or "tabla"


class DuckDBEngine:
    """Envoltorio sobre DuckDB en memoria con registro de DataFrames."""

    def __init__(self) -> None:
        if not HAS_DUCKDB:
            raise ImportError("duckdb no está instalado. Añádelo a requirements.txt.")
        self.con = duckdb.connect(database=":memory:")

    def register(self, name: str, df: pd.DataFrame) -> str:
        table = sanitize_table_name(name)
        self.con.register(table, df)
        return table

    def query(self, sql: str) -> pd.DataFrame:
        return self.con.execute(sql).df()

    def list_tables(self) -> List[Tuple[str, int]]:
        tables = self.con.execute("SHOW TABLES").fetchall()
        return [
            (t[0], self.con.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0])
            for t in tables
        ]

    def describe(self, table: str) -> pd.DataFrame:
        return self.con.execute(f"DESCRIBE {table}").df()

    def close(self) -> None:
        try:
            self.con.close()
        except Exception:  # pragma: no cover
            pass

    def __enter__(self) -> "DuckDBEngine":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
