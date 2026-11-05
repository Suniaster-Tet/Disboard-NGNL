"""Catálogo interactivo de esquemas de datos.

Registra metadatos de cada archivo: columnas originales, nombres
estandarizados, fusiones, PKs y FKs. **No almacena DataFrames** en el
catálogo (eso es responsabilidad de Izuna al construir la base en RAM).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import pandas as pd

from tools.data_loader import (
    apply_filters_interactive,
    read_csv_safe,
    read_excel_sheet,
    list_sheets,
    select_file,
    select_sheet_interactive,
)


def normalize_column_name(name: str) -> str:
    return (
        str(name).strip().lower()
        .replace(" ", "_").replace(".", "")
        .replace("-", "_").replace("/", "_")
    )


def simple_similarity(s1: str, s2: str) -> float:
    s1, s2 = s1.lower().strip(), s2.lower().strip()
    if s1 == s2:
        return 1.0
    if s1 in s2 or s2 in s1:
        return 0.8
    common = set(s1) & set(s2)
    return len(common) / max(len(set(s1)), len(set(s2)))


class DataCatalog:
    """Acumula esquemas de archivos procesados."""

    def __init__(self) -> None:
        self.files: dict[str, dict[str, Any]] = {}
        self.used_names: list[str] = []
        self.field_dictionary: dict[str, dict[str, Any]] = {}

    def register(self, filename: str, schema: dict[str, Any]) -> None:
        self.files[filename] = schema

    def summary(self) -> dict[str, Any]:
        return {
            "total_files": len(self.files),
            "standardized_names": len(self.used_names),
            "field_dictionary": len(self.field_dictionary),
        }


def build_interactive_catalog(reporters: Optional[list] = None) -> DataCatalog:
    """Construye el catálogo de forma interactiva a partir de archivos del usuario."""
    if reporters is None:
        reporters = []

    catalog = DataCatalog()

    while True:
        path = select_file()
        if path is None:
            break

        df, sheet = select_sheet_interactive(path)
        if df is None or df.empty:
            print(f"⚠️ Empty or unreadable file: {path}")
            continue

        print(f"\nPreview of {Path(path).name} (sheet: {sheet}):")
        for i, col in enumerate(df.columns, 1):
            sample = df[col].dropna().astype(str).head(1)
            print(f"  [{i}] {col} → {sample.iloc[0] if not sample.empty else '[empty]'}")

        df = apply_filters_interactive(df)

        mapping: dict[str, str] = {}
        for col in df.columns:
            suggestion = normalize_column_name(col)
            entry = input(f"Standardized name for '{col}' [Enter = '{suggestion}']: ").strip()
            final = entry or suggestion
            mapping[col] = final
            if final not in catalog.used_names:
                catalog.used_names.append(final)

        cols = list(df.columns)
        pk_input = input("PK columns (comma-separated numbers, Enter = none): ").strip()
        fk_input = input("FK columns (comma-separated numbers, Enter = none): ").strip()

        def _parse(text: str) -> list[str]:
            out = []
            for x in text.replace(";", ",").split(","):
                x = x.strip()
                if x.isdigit():
                    j = int(x) - 1
                    if 0 <= j < len(cols):
                        out.append(mapping[cols[j]])
            return out

        schema = {
            "path": str(Path(path).resolve()),
            "sheet": sheet,
            "original_columns": cols,
            "column_mapping": mapping,
            "standardized_columns": list(mapping.values()),
            "primary_keys": _parse(pk_input),
            "foreign_keys": _parse(fk_input),
        }
        catalog.register(Path(path).name, schema)

        if input("\nAdd another file? (y/N): ").strip().lower() != "y":
            break

    for r in reporters:
        if hasattr(r, "register_action"):
            r.register_action(
                title="Data catalog construction",
                inputs=catalog.summary(),
            )
    return catalog
