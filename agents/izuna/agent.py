"""Izuna — Ingeniería de Datos (con integración tensorial)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from agents.base import Agent
from agents.izuna.tensor_db import TensorDB
from agents.izuna.tensor_schema import df_to_tensor
from core.state_schema import OverallState


class IzunaDataEngineer(Agent):
    nombre = "Izuna"
    rol = "HPC e Ingeniería de Datos / Subagente de Shiro"

    def __init__(
        self,
        edge_id: Optional[str] = None,
        tensor_db: Optional[TensorDB] = None,
    ):
        super().__init__(edge_id)
        self.db = tensor_db or TensorDB()

    # ------------------------------------------------------------------ #
    # API para Shiro
    # ------------------------------------------------------------------ #
    def list_tensors(self) -> List[Dict[str, Any]]:
        return self.db.list_tensors()

    def get_tensor(self, name: str) -> Optional[Dict[str, Any]]:
        return self.db.get_tensor(name)

    def project(self, name: str, dimensions: List[str]) -> Dict[str, Any]:
        return self.db.project(name, dimensions)

    def aggregate(
        self, name: str, by: List[str], metric: str, operation: str = "sum"
    ) -> Dict[str, Any]:
        return self.db.aggregate(name, by, metric, operation)

    def verify_tensor(self, name: str) -> bool:
        return self.db.verify(name)

    def register_dataframe(
        self, df: pd.DataFrame, name: str, source: str = ""
    ) -> str:
        tensor = df_to_tensor(df, name=name, source=source)
        self.db.register_tensor(tensor)
        return tensor["schema"]["name"]

    # ------------------------------------------------------------------ #
    # Resumen
    # ------------------------------------------------------------------ #
    def summary(self) -> Dict[str, Any]:
        return self.db.estado()

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #
    def execute(self, state: OverallState) -> OverallState:
        self.register("izuna_ready", self.db.estado())
        state["current_step"] = "shiro_execution"
        return state
