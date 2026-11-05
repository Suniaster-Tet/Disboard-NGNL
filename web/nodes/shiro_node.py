"""Nodo Shiro: ejecución técnica."""
from __future__ import annotations

from agents.shiro.agent import ShiroAnalyst
from core.state_schema import OverallState


def shiro_node(state: OverallState) -> OverallState:
    edge_id = state.get("edge_id", "edge-default")
    shiro = ShiroAnalyst(edge_id=edge_id)

    results = []
    for d in state.get("entregables", []):
        if d.get("agente_asignado") != "Shiro":
            continue
        code, test = shiro.generate_tdd_code(d.get("descripcion", ""))
        results.append({"entregable": d["id"], "code": code, "test": test})

    state.setdefault("action_details", {})["shiro_results"] = results
    state["current_step"] = "shiro"
    state["next_agent"] = "supervisor"
    return state
