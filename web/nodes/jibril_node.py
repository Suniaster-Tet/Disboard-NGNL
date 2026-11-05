"""Nodo Jibril: enriquecimiento bibliográfico."""
from __future__ import annotations

from agents.jibril.agent import JibrilScientific
from core.state_schema import OverallState


def jibril_node(state: OverallState) -> OverallState:
    edge_id = state.get("edge_id", "edge-default")
    jibril = JibrilScientific(edge_id=edge_id)
    dois = state.get("action_details", {}).get("dois", [])

    result = jibril.fetch_many(dois)
    state["bibliography"] = state.get("bibliography", []) + result["ok"]
    action_details = state.setdefault("action_details", {})
    action_details["jibril_rejected"] = result["rejected"]
    action_details["jibril_verified"] = result["ok"]
    for deliverable in state.get("entregables", []):
        if deliverable.get("agente_asignado") == "Jibril":
            deliverable["estado"] = "entregado"
    state["current_step"] = "jibril"
    state["next_agent"] = "supervisor"
    return state
