"""Sora — El Estratega (Project Manager)."""
from __future__ import annotations

from typing import Any, Dict, List

from agents.base import Agent
from core.contract import Contract
from core.edge import Edge
from core.state_schema import OverallState


class SoraStrategist(Agent):
    nombre = "Sora"
    rol = "Estratega principal / Project Manager"

    # ------------------------------------------------------------------ #
    # Planificación
    # ------------------------------------------------------------------ #
    def plan_edge(self, edge_id: str, seed_prompt: str) -> Dict[str, Any]:
        """Descompone la idea semilla en objetivos, metas y entregables."""
        self.register("plan_started", {"edge_id": edge_id, "seed": seed_prompt[:80]})

        objetivos = [
            f"Responder a la idea semilla: {seed_prompt[:80]}",
            "Producir entregables verificables con trazabilidad",
        ]
        metas = [
            "Plan aprobado por Tet",
            "Evidencia bibliográfica verificada (DOI)",
            "Código y cálculos reproducibles",
        ]
        entregables = [
            {"id": "E1", "descripcion": "Plan y contrato del edge",
             "agente_asignado": "Sora", "estado": "pendiente"},
            {"id": "E2", "descripcion": "Bibliografía enriquecida con DOI",
             "agente_asignado": "Jibril", "estado": "pendiente"},
            {"id": "E3", "descripcion": "Código y cálculos del proyecto",
             "agente_asignado": "Shiro", "estado": "pendiente"},
            {"id": "E4", "descripcion": "Auditoría de alineación",
             "agente_asignado": "Chlammy", "estado": "pendiente"},
        ]
        return {
            "edge_id": edge_id,
            "objetivos": objetivos,
            "metas": metas,
            "entregables": entregables,
            "avance": 0,
            "prioridad": self._priority_for(entregables),
        }

    def plan_from_contract(self, edge: Edge, contract: Contract) -> Dict[str, Any]:
        """Reconstruye el plan de Sora a partir de un contrato ya aprobado."""
        return {
            "edge_id": edge.id,
            "objetivos": list(contract.objetivos),
            "metas": list(contract.metas),
            "entregables": [dict(e) for e in contract.entregables],
            "avance": edge.avance,
            "prioridad": edge.prioridad,
        }

    @staticmethod
    def _priority_for(entregables: List[Dict[str, Any]]) -> str:
        pendientes = sum(1 for e in entregables if e.get("estado") == "pendiente")
        if pendientes >= 4:
            return "alta"
        if pendientes >= 1:
            return "media"
        return "baja"

    # ------------------------------------------------------------------ #
    # Enrutamiento
    # ------------------------------------------------------------------ #
    def next_step(self, state: OverallState) -> str:
        """Decide qué agente sigue según los entregables pendientes.

        Devuelve uno de: "jibril", "shiro", "chlammy", "hitl", "fin".
        """
        entregables = state.get("entregables", [])
        pendientes = [e for e in entregables if e.get("estado", "pendiente") == "pendiente"]
        if not pendientes:
            return "fin" if state.get("status") == "COMPLETO" else "hitl"

        # Orden por dependencia: bibliografía -> ejecución -> auditoría
        prioridad = ["Jibril", "Shiro", "Chlammy"]
        for agente in prioridad:
            if any(p.get("agente_asignado") == agente for p in pendientes):
                return agente.lower()
        # Si el agente no está en la lista, se envía a Shiro por defecto
        return "shiro"

    # ------------------------------------------------------------------ #
    # Avance
    # ------------------------------------------------------------------ #
    @staticmethod
    def estimar_avance(state: OverallState) -> int:
        entregables = state.get("entregables", [])
        if not entregables:
            return 0
        entregados = sum(1 for e in entregables if e.get("estado") == "entregado")
        return int(round(entregados / len(entregables) * 100))

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #
    def execute(self, state: OverallState) -> OverallState:
        plan = self.plan_edge(
            state.get("edge_id", "edge-default"),
            state.get("seed", ""),
        )
        state.update(plan)
        state["current_step"] = "supervisor"
        state["next_agent"] = self.next_step(state)
        self.register("plan_generated", {"entregables": len(plan["entregables"])})
        return state
