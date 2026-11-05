"""Nodo HITL: pausa el grafo y espera a Tet (LangGraph interrupt)."""
from __future__ import annotations

from langgraph.types import interrupt

from core.hitl import solicitar_aprobacion_tet
from core.state_schema import OverallState


def hitl_node(state: OverallState) -> OverallState:
    """Pausa el grafo para que Tet apruebe, modifique o rechace."""
    payload = {
        "edge_id": state.get("edge_id"),
        "action_details": state.get("action_details", {}),
    }
    # interrupt() pausa el grafo y devuelve el veredicto cuando se resume.
    veredicto = interrupt(payload)
    state["tet_feedback"] = str(veredicto) if veredicto is not None else ""
    decision, state = solicitar_aprobacion_tet(state)
    if decision == "proceed":
        state["current_step"] = "fin"
        state["next_agent"] = "fin"
    elif decision == "rollback":
        state["current_step"] = "supervisor"
        state["next_agent"] = "supervisor"
    else:
        state["current_step"] = "shiro"
        state["next_agent"] = "shiro"
    return state
