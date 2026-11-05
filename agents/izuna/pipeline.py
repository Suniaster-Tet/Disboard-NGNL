"""Pipeline de Izuna: catálogo → DuckDB → tabla maestra → tensores → Shiro.

Orquesta el flujo completo de ingeniería de datos:
1. Construye un catálogo interactivo de esquemas (`tools.data_catalog`).
2. Registra cada DataFrame en DuckDB en memoria (`DuckDBEngine`).
3. Convierte cada tabla en un tensor y lo persiste (`TensorDB`).
4. Construye la tabla maestra de autoridades y la registra como tensor.
5. Registra cada paso en el log del edge (si se proporciona `edge_id`).

El pipeline no escribe archivos de salida; solo registra tensores en
`logs/tensor_db.jsonl` y deja que Shiro consuma los tensores vía
`IzunaDataEngineer`. Los reporteros (si se pasan) reciben el resumen.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

import pandas as pd

from agents.izuna.authorities import build_master_table
from agents.izuna.duckdb_engine import DuckDBEngine
from agents.izuna.tensor_db import TensorDB
from agents.izuna.tensor_schema import df_to_tensor
from core.log import Log
from tools.data_catalog import DataCatalog, build_interactive_catalog


def _safe_read(schema: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Lee un archivo del catálogo aplicando el mapeo de columnas."""
    path = schema["path"]
    sheet = schema.get("sheet")
    try:
        df = (
            pd.read_csv(path)
            if str(path).lower().endswith(".csv")
            else pd.read_excel(path, sheet_name=sheet or 0)
        )
    except (FileNotFoundError, PermissionError, ValueError):
        return None
    mapping = schema.get("column_mapping", {})
    if mapping:
        df = df.rename(columns=mapping)
    return df


def run_izuna_pipeline(
    reporters: Optional[List[Any]] = None,
    edge_id: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """Ejecuta el pipeline completo de Izuna.

    Args:
        reporters: lista opcional de `tools.reporter.Reporter` para dejar
            constancia del proceso.
        edge_id: si se indica, cada paso se registra en `edges/<id>/log.jsonl`.
        progress_callback: función opcional que recibe un mensaje de progreso.

    Returns:
        Dict con:
            - status: "ok" | "empty" | "error"
            - catalog: resumen del catálogo
            - duckdb_tables: lista de (tabla, filas)
            - tensors: nombres de tensores registrados
            - tensor_db_state: estado del TensorDB
            - errors: lista de archivos con error
    """
    reporters = reporters or []
    log = Log(edge_id) if edge_id else None

    def _progress(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    tensor_db = TensorDB()
    catalog: DataCatalog = build_interactive_catalog(reporters=reporters)

    if not catalog.files:
        if log:
            log.registrar("izuna_pipeline_empty", nivel="WARNING")
        return {"status": "empty"}

    dataframes: Dict[str, pd.DataFrame] = {}
    engine = DuckDBEngine()
    tensors_registered: List[str] = []
    errors: List[Dict[str, str]] = []

    try:
        for name, schema in catalog.files.items():
            df = _safe_read(schema)
            if df is None or df.empty:
                errors.append({"file": name, "error": "unreadable_or_empty"})
                if log:
                    log.registrar(
                        "izuna_file_error",
                        {"file": name, "error": "unreadable_or_empty"},
                        nivel="ERROR",
                    )
                _progress(f"Error: {name}")
                continue

            dataframes[name] = df

            # 1. DuckDB
            table = engine.register(name, df)
            _progress(f"DuckDB: {table} ({len(df)} filas)")
            if log:
                log.registrar(
                    "izuna_duckdb_registered",
                    {"table": table, "rows": len(df)},
                )

            # 2. Tensor
            tensor = df_to_tensor(df, name=f"tensor_{name}", source=str(schema["path"]))
            tensor_db.register_tensor(tensor)
            tensors_registered.append(tensor["schema"]["name"])
            _progress(f"Tensor: {tensor['schema']['name']}")
            if log:
                log.registrar(
                    "izuna_tensor_registered",
                    {"tensor": tensor["schema"]["name"]},
                )

        # 3. Tabla maestra de autoridades
        master = build_master_table(catalog.files, dataframes)
        if not master.empty:
            engine.register("master_authorities", master)
            master_tensor = df_to_tensor(
                master,
                name="tensor_authorities",
                dimensions=[
                    "hash_id",
                    "nombres_oficiales",
                    "apellidos_oficiales",
                    "fuente",
                ],
                source="authorities",
            )
            tensor_db.register_tensor(master_tensor)
            tensors_registered.append("tensor_authorities")
            _progress(f"Master: {len(master)} autoridades")
            if log:
                log.registrar("izuna_master_registered", {"rows": len(master)})

        result = {
            "status": "ok",
            "catalog": catalog.summary(),
            "duckdb_tables": engine.list_tables(),
            "tensors": tensors_registered,
            "tensor_db_state": tensor_db.estado(),
            "errors": errors,
        }

        if log:
            log.registrar("izuna_pipeline_finished", result)

        return result

    except Exception as e:
        if log:
            log.registrar(
                "izuna_pipeline_error",
                {"error": str(e)},
                nivel="ERROR",
            )
        return {
            "status": "error",
            "error": str(e),
            "tensors": tensors_registered,
            "errors": errors,
        }
    finally:
        engine.close()
