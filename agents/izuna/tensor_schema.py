"""Esquema y conversión de tensores para Izuna.

Un tensor es un array multidimensional indexado por claves, con metadatos.
Esta capa convierte DataFrames en tensores y viceversa.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_dataframe(df: pd.DataFrame) -> str:
    payload = df.to_json(orient="records", force_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass
class TensorSchema:
    """Metadatos de un tensor."""
    name: str
    dimensions: List[str]
    types: Dict[str, str]
    source: str
    hash_sha256: str = ""
    created_at: str = field(default_factory=_utcnow)
    records: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TensorSchema":
        return cls(
            name=data["name"],
            dimensions=list(data["dimensions"]),
            types=dict(data["types"]),
            source=data.get("source", ""),
            hash_sha256=data.get("hash_sha256", ""),
            created_at=data.get("created_at", _utcnow()),
            records=int(data.get("records", 0)),
        )

    @classmethod
    def from_dataframe(
        cls,
        name: str,
        df: pd.DataFrame,
        dimensions: Optional[List[str]] = None,
        source: str = "",
    ) -> "TensorSchema":
        dims = dimensions or list(df.columns)
        types = {str(c): str(t) for c, t in df.dtypes.items()}
        return cls(
            name=name,
            dimensions=dims,
            types=types,
            source=source,
            hash_sha256=hash_dataframe(df),
            records=len(df),
        )


def df_to_tensor(
    df: pd.DataFrame,
    name: str,
    dimensions: Optional[List[str]] = None,
    source: str = "",
) -> Dict[str, Any]:
    """Convierte un DataFrame en un tensor serializable."""
    schema = TensorSchema.from_dataframe(name, df, dimensions, source)
    return {"schema": schema.to_dict(), "data": df.to_dict(orient="records")}


def tensor_to_df(tensor: Dict[str, Any]) -> pd.DataFrame:
    """Reconstruye un DataFrame desde un tensor serializable."""
    return pd.DataFrame(tensor.get("data", []))


def project_tensor(tensor: Dict[str, Any], dimensions: List[str]) -> Dict[str, Any]:
    """Proyecta un tensor sobre un subconjunto de dimensiones."""
    df = tensor_to_df(tensor)
    missing = [d for d in dimensions if d not in df.columns]
    if missing:
        raise KeyError(f"Dimensiones no presentes en el tensor: {missing}")
    projected = df[dimensions]
    schema = TensorSchema.from_dataframe(
        f"{tensor['schema']['name']}_projection",
        projected,
        dimensions,
        tensor["schema"].get("source", ""),
    )
    return {"schema": schema.to_dict(), "data": projected.to_dict(orient="records")}


def aggregate_tensor(
    tensor: Dict[str, Any],
    by: List[str],
    metric: str,
    operation: str = "sum",
) -> Dict[str, Any]:
    """Agrega un tensor agrupando por dimensiones y aplicando una operación."""
    df = tensor_to_df(tensor)
    if metric not in df.columns:
        raise KeyError(f"Métrica no encontrada: {metric}")
    if operation not in {"sum", "mean", "count", "min", "max"}:
        raise ValueError(f"Operación no soportada: {operation}")

    agg = df.groupby(by, dropna=False)[metric].agg(operation).reset_index()
    name = f"{tensor['schema']['name']}_{operation}_{metric}"
    schema = TensorSchema.from_dataframe(
        name, agg, by + [metric], tensor["schema"].get("source", "")
    )
    return {"schema": schema.to_dict(), "data": agg.to_dict(orient="records")}
