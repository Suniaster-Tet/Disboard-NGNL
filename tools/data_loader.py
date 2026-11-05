"""Carga determinista de datos tabulares con Polars/Pandas.

- Lectura segura de CSV con múltiples codificaciones.
- Selección interactiva de archivo, hoja y filtros.
- Guardado de base inicial con ruta configurable.

Las funciones puras (`read_csv_safe`, `read_excel_sheet`, `filter_by_values`)
son testeables. Las funciones `select_*` son interactivas.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Sequence, Union

import pandas as pd

try:
    import polars as pl
    HAS_POLARS = True
except ImportError:  # pragma: no cover
    pl = None
    HAS_POLARS = False


def read_csv_safe(path: Union[str, Path]) -> pd.DataFrame:
    """Lee un CSV probando varias codificaciones hasta que una funcione."""
    last_error: Optional[Exception] = None
    for encoding in ("utf-8", "utf-8-sig", "latin1", "cp1252"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except (UnicodeDecodeError, pd.errors.ParserError) as e:
            last_error = e
    if last_error:
        raise last_error
    raise ValueError(f"Could not read CSV: {path}")


def read_excel_sheet(path: Union[str, Path], sheet: Optional[str] = None) -> pd.DataFrame:
    """Lee una hoja específica de un Excel o la primera si no se indica."""
    if sheet is None:
        return pd.read_excel(path, sheet_name=0)
    return pd.read_excel(path, sheet_name=sheet)


def list_sheets(path: Union[str, Path]) -> list[str]:
    return pd.ExcelFile(path).sheet_names


def filter_by_values(
    df: pd.DataFrame, column: str, values: Sequence[Any], include: bool = True
) -> pd.DataFrame:
    """Filtra un DataFrame por una lista de valores (incluir o excluir)."""
    serie = df[column].fillna("").astype(str)
    mask = serie.isin([str(v) for v in values])
    return df[mask] if include else df[~mask]


def save_initial_base(
    df: pd.DataFrame,
    output_dir: Union[str, Path] = ".",
    name: Optional[str] = None,
) -> str:
    """Guarda el DataFrame como XLSX y devuelve la ruta absoluta."""
    date = datetime.now().strftime("%Y%m%d")
    name = name or f"initial_base_{date}.xlsx"
    if not name.endswith(".xlsx"):
        name += ".xlsx"
    path = Path(output_dir) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(path, index=False)
    return str(path.resolve())


def select_file(start_dir: Union[str, Path] = ".") -> Optional[str]:
    """Selecciona un archivo XLSX/CSV de forma interactiva."""
    folder = Path(start_dir)
    if not folder.exists():
        print(f"⚠️ Folder does not exist: {folder}")
        return None

    files = sorted(
        f for f in os.listdir(folder)
        if f.lower().endswith((".xlsx", ".xls", ".csv"))
    )
    if not files:
        print(f"⚠️ No XLSX/CSV files in {folder}.")
        return None

    print("\nFiles found:")
    for i, file in enumerate(files, 1):
        size_mb = (folder / file).stat().st_size / 1024 / 1024
        print(f"  [{i}] {file} ({size_mb:.2f} MB)")

    while True:
        choice = input("\nSelect file (0 = cancel): ").strip()
        if choice == "0":
            return None
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(files):
                return str((folder / files[idx]).resolve())
        except ValueError:
            pass
        print("⚠️ Invalid selection.")


def select_sheet_interactive(path: Union[str, Path]) -> tuple[Optional[pd.DataFrame], Optional[str]]:
    """Selecciona interactivamente una hoja de Excel o carga un CSV."""
    if str(path).lower().endswith(".csv"):
        try:
            df = read_csv_safe(path)
            print(f"✅ CSV loaded: {len(df)} rows, {len(df.columns)} columns.")
            return df, "CSV"
        except Exception as e:
            print(f"⚠️ Error reading CSV: {e}")
            return None, None

    try:
        sheets = list_sheets(path)
    except Exception as e:
        print(f"⚠️ Error opening Excel: {e}")
        return None, None

    print("\nAvailable sheets:")
    for i, sheet in enumerate(sheets, 1):
        print(f"  [{i}] {sheet}")

    while True:
        choice = input("\nSelect sheet (0 = cancel): ").strip()
        if choice == "0":
            return None, None
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(sheets):
                sheet = sheets[idx]
                return read_excel_sheet(path, sheet), sheet
        except ValueError:
            pass
        print("⚠️ Invalid selection.")


def apply_filters_interactive(df: pd.DataFrame) -> pd.DataFrame:
    """Permite aplicar filtros sucesivos sobre columnas del DataFrame."""
    if df.empty:
        print("⚠️ DataFrame is empty.")
        return df

    while True:
        print(f"\nCurrent rows: {len(df)}")
        for i, col in enumerate(df.columns, 1):
            print(f"  [{i}] {col}")
        choice = input("\nColumn to filter (0 = finish): ").strip()
        try:
            idx = int(choice)
        except ValueError:
            continue
        if idx == 0:
            return df
        if not (1 <= idx <= len(df.columns)):
            continue

        column = df.columns[idx - 1]
        values = sorted(df[column].fillna("").astype(str).unique())
        print(f"\nUnique values in '{column}' (max 30):")
        for i, v in enumerate(values[:30], 1):
            print(f"  [{i}] {v}")

        mode = input("\n[1] Include  [2] Exclude  (0 = cancel): ").strip()
        if mode == "0":
            continue
        if mode not in {"1", "2"}:
            continue

        selected = input("Numbers separated by comma: ").strip()
        indices = []
        for x in selected.split(","):
            try:
                j = int(x.strip()) - 1
                if 0 <= j < len(values):
                    indices.append(j)
            except ValueError:
                pass
        if not indices:
            continue

        target_values = [values[j] for j in indices]
        df = filter_by_values(df, column, target_values, include=(mode == "1"))
        print(f"✅ Rows after filter: {len(df)}")


def load_tabular(path: Union[str, Path]) -> dict[str, Any]:
    """Carga un CSV/XLSX con Polars si está disponible, si no con Pandas."""
    path = Path(path)
    if not path.exists():
        return {"status": "error", "message": f"File not found: {path}"}

    try:
        if HAS_POLARS:
            df = pl.read_csv(path) if path.suffix == ".csv" else pl.read_excel(path)
            return {
                "status": "success",
                "engine": "polars",
                "rows": len(df),
                "columns": df.columns,
                "schema": {c: str(t) for c, t in zip(df.columns, df.dtypes)},
            }
        df = read_csv_safe(path) if path.suffix == ".csv" else read_excel_sheet(path)
        return {
            "status": "success",
            "engine": "pandas",
            "rows": len(df),
            "columns": list(df.columns),
            "schema": {c: str(t) for c, t in df.dtypes.items()},
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
