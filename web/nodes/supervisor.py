"""Nodo supervisor del grafo (Sora)."""
from __future__ import annotations

from agents.sora.agent import SoraStrategist
from core.state_schema import OverallState


def supervisor_node(state: OverallState) -> OverallState:
    edge_id = state.get("edge_id", "edge-default")
    sora = SoraStrategist(edge_id=edge_id)
    if not state.get("objetivos"):
        plan = sora.plan_edge(edge_id, state.get("seed", ""))
        state.update(plan)
        state.setdefault("action_details", {})["contract"] = {
            "objetivos": plan["objetivos"],
            "entregables": plan["entregables"],
        }
        for deliverable in state.get("entregables", []):
            if deliverable.get("agente_asignado") == "Sora":
                deliverable["estado"] = "entregado"
    # Enrutar al primer entregable pendiente
    pendientes = [e for e in state.get("entregables", [])
                  if e.get("estado", "pendiente") == "pendiente"]
    if not pendientes:
        state["next_agent"] = "fin" if state.get("status") == "COMPLETO" else "hitl"
    else:
        orden = {"Jibril": 0, "Shiro": 1, "Chlammy": 2, "Chlammy Zell": 2}
        asignado = min(
            pendientes,
            key=lambda item: orden.get(item.get("agente_asignado", "Shiro"), 1),
        ).get("agente_asignado", "Shiro")
        state["next_agent"] = "chlammy" if asignado == "Chlammy Zell" else asignado.lower()
        state["assigned_agent"] = asignado
    state["current_step"] = "supervisor"
    return state
