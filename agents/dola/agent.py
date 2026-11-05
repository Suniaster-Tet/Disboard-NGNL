"""Stephanie Dola — Orquestadora y Diplomática."""
from __future__ import annotations

from typing import Any, Dict

from agents.base import Agent
from core.log import Log
from core.state_schema import OverallState

PAID_PROVIDERS = {"anthropic", "openai", "deepseek"}


class StephanieOrchestrator(Agent):
    nombre = "Stephanie Dola"
    rol = "Orquestadora / Diplomática"

    def __init__(self, edge_id: str | None = None, config: Dict[str, Any] | None = None):
        super().__init__(edge_id)
        self.config = config or {}
        self.strict_free_tier = self.config.get("strict_free_tier_only", True)
        self.confirm_paid_fallback = self.config.get("confirm_before_paid_fallback", True)

    # ------------------------------------------------------------------ #
    # Clasificación
    # ------------------------------------------------------------------ #
    def classify_task(self, task_payload: Dict[str, Any]) -> str:
        """Devuelve 'local', 'free' o 'paid' según el proveedor solicitado."""
        provider = str(task_payload.get("provider", "free")).lower()
        if provider == "ollama":
            return "local"
        if provider in PAID_PROVIDERS:
            return "paid"
        return "free"

    # ------------------------------------------------------------------ #
    # Enrutamiento
    # ------------------------------------------------------------------ #
    def route_agent_task(
        self, agent_name: str, task_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        kind = self.classify_task(task_payload)
        if kind == "paid" and self.confirm_paid_fallback:
            return {
                "status": "interrupt_required",
                "reason": (
                    f"'{agent_name}' requiere '{task_payload.get('provider')}' (pago). "
                    "Confirmación de Tet requerida."
                ),
                "action": "await_tet_confirmation",
            }
        return {
            "status": "proceed",
            "agent": agent_name,
            "provider": task_payload.get("provider", "free"),
            "kind": kind,
            "payload": task_payload,
        }

    # ------------------------------------------------------------------ #
    # Rollback
    # ------------------------------------------------------------------ #
    @staticmethod
    def rollback_reason(state: OverallState) -> str:
        return (
            f"Tet rechazó el paso '{state.get('current_step', '?')}'. "
            f"Entregable: {state.get('assigned_agent', '?')}."
        )

    def register_rollback(self, edge_id: str, reason: str) -> None:
        self.register("rollback", {"edge_id": edge_id, "reason": reason}, level="WARNING")
        Log(edge_id).registrar(
            "rollback", {"reason": reason}, agente=self.nombre, nivel="WARNING"
        )

    def execute_rollback(self, edge_id: str, reason: str) -> Dict[str, Any]:
        self.register_rollback(edge_id, reason)
        return {
            "status": "rollback_completed",
            "edge_id": edge_id,
            "reason": reason,
        }

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #
    def execute(self, state: OverallState) -> OverallState:
        state["current_step"] = "sora_plan"
        self.register("orchestration_started", {"edge_id": state.get("edge_id")})
        return state
