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
    # Enrutar al primer entregable pendiente
    pendientes = [e for e in state.get("entregables", [])
                  if e.get("estado", "pendiente") == "pendiente"]
    if not pendientes:
        state["next_agent"] = "fin"
    else:
        asignado = pendientes[0].get("agente_asignado", "Shiro")
        state["next_agent"] = asignado.lower()
        state["assigned_agent"] = asignado
    state["current_step"] = "supervisor"
    return state
