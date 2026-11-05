"""Base de datos tensorial de Izuna.

Almacena tensores serializados en JSONL, indexados por nombre y dimensiones.
Referencia conceptual: arXiv:2211.02753v1 (tensor data model).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.izuna.tensor_schema import (
    TensorSchema,
    aggregate_tensor,
    df_to_tensor,
    project_tensor,
    tensor_to_df,
)


class TensorDB:
    """Base de datos tensorial local."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or Path("logs/tensor_db.jsonl")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    # ------------------------------------------------------------------ #
    # Ingesta
    # ------------------------------------------------------------------ #
    def insert(self, record: Dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def register_tensor(self, tensor: Dict[str, Any]) -> None:
        if "schema" not in tensor or "data" not in tensor:
            raise ValueError("El tensor debe tener 'schema' y 'data'.")
        self.insert({"type": "tensor", **tensor})

    def delete_tensor(self, name: str) -> bool:
        if not self.path.exists():
            return False
        lines = self.path.read_text(encoding="utf-8").splitlines()
        new_lines = []
        deleted = False
        for line in lines:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                new_lines.append(line)
                continue
            if r.get("type") == "tensor" and r.get("schema", {}).get("name") == name:
                deleted = True
                continue
            new_lines.append(line)
        if deleted:
            self.path.write_text("\n".join(new_lines) + ("\n" if new_lines else ""), encoding="utf-8")
        return deleted

    # ------------------------------------------------------------------ #
    # Consulta
    # ------------------------------------------------------------------ #
    def query(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self.path.open("r", encoding="utf-8") as f:
            return [json.loads(l) for i, l in enumerate(f) if i < limit and l.strip()]

    def list_tensors(self) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                if r.get("type") == "tensor":
                    result.append(r["schema"])
        return result

    def get_tensor(self, name: str) -> Optional[Dict[str, Any]]:
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                if r.get("type") == "tensor" and r["schema"].get("name") == name:
                    return r
        return None

    def count(self) -> int:
        return sum(1 for _ in self.path.open())

    # ------------------------------------------------------------------ #
    # Operaciones tensoriales
    # ------------------------------------------------------------------ #
    def project(self, name: str, dimensions: List[str]) -> Dict[str, Any]:
        tensor = self.get_tensor(name)
        if tensor is None:
            raise KeyError(f"Tensor no encontrado: {name}")
        projected = project_tensor(tensor, dimensions)
        self.register_tensor(projected)
        return projected

    def aggregate(
        self,
        name: str,
        by: List[str],
        metric: str,
        operation: str = "sum",
    ) -> Dict[str, Any]:
        tensor = self.get_tensor(name)
        if tensor is None:
            raise KeyError(f"Tensor no encontrado: {name}")
        aggregated = aggregate_tensor(tensor, by, metric, operation)
        self.register_tensor(aggregated)
        return aggregated

    # ------------------------------------------------------------------ #
    # Integridad y estado
    # ------------------------------------------------------------------ #
    def verify(self, name: str) -> bool:
        tensor = self.get_tensor(name)
        if tensor is None:
            return False
        df = tensor_to_df(tensor)
        schema = TensorSchema.from_dataframe(
            tensor["schema"]["name"],
            df,
            tensor["schema"].get("dimensions"),
            tensor["schema"].get("source", ""),
        )
        return schema.hash_sha256 == tensor["schema"].get("hash_sha256")

    def estado(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "records": self.count(),
            "tensors": len(self.list_tensors()),
        }
