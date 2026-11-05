"""Construcción de la tabla maestra de autoridades."""
from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any, Dict

import pandas as pd


def normalize_text(value: Any) -> str:
    if not isinstance(value, str) or pd.isna(value):
        return ""
    t = unicodedata.normalize("NFD", value)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", t.upper().strip())


def parse_name_with_comma(value: Any) -> tuple[str, str]:
    """Devuelve (nombres, apellidos) si el valor tiene formato 'APELLIDOS, NOMBRES'."""
    if not isinstance(value, str) or pd.isna(value) or not value.strip():
        return "", ""
    if "," in value:
        ap, nom = value.split(",", 1)
        return normalize_text(nom), normalize_text(ap)
    return normalize_text(value), ""


def _short_hash(*parts: str) -> str:
    payload = "|".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def build_master_table(
    catalogs: Dict[str, Dict[str, Any]],
    dataframes: Dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Construye la tabla maestra a partir de los DataFrames ya procesados."""
    rows = []
    for name, schema in catalogs.items():
        df = dataframes.get(name)
        if df is None or df.empty:
            continue

        cols = list(df.columns)
        name_candidates = [
            c for c in cols
            if any(k in c.lower() for k in ("nombre", "nombres", "autoridad", "investigador"))
        ]
        surname_candidates = [
            c for c in cols
            if any(k in c.lower() for k in ("apellido", "apellidos", "paterno"))
        ]

        if not name_candidates and not surname_candidates:
            continue

        for _, row in df.iterrows():
            names = " ".join(normalize_text(row[c]) for c in name_candidates).strip()
            surnames = " ".join(normalize_text(row[c]) for c in surname_candidates).strip()

            if not names and not surnames:
                continue

            row_key = _short_hash(names, surnames, name)
            rows.append({
                "hash_id": row_key,
                "nombres_oficiales": names,
                "apellidos_oficiales": surnames,
                "formato_nombre_apellido": f"{names} {surnames}".strip(),
                "formato_apellido_nombre": f"{surnames} {names}".strip(),
                "fuente": name,
            })

    df_out = pd.DataFrame(rows, columns=[
        "hash_id", "nombres_oficiales", "apellidos_oficiales",
        "formato_nombre_apellido", "formato_apellido_nombre", "fuente",
    ])
    return df_out.drop_duplicates(subset=["hash_id"]).reset_index(drop=True)
