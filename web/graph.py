"""Grafo LangGraph del tablero web (patrón supervisor)."""
from __future__ import annotations

from langgraph.graph import END, StateGraph

from core.state_schema import OverallState
from web.checkpointer import WebCheckpointer
from web.nodes import (
    chlammy_node, hitl_node, jibril_node, shiro_node, supervisor_node,
)


def _route(state: OverallState) -> str:
    return state.get("next_agent", "fin")


def build_graph() -> StateGraph:
    g = StateGraph(OverallState)
    g.add_node("supervisor", supervisor_node)
    g.add_node("jibril", jibril_node)
    g.add_node("shiro", shiro_node)
    g.add_node("chlammy", chlammy_node)
    g.add_node("hitl", hitl_node)

    g.set_entry_point("supervisor")

    g.add_conditional_edges("supervisor", _route, {
        "jibril": "jibril",
        "shiro": "shiro",
        "chlammy": "chlammy",
        "hitl": "hitl",
        "fin": END,
    })
    g.add_edge("jibril", "supervisor")
    g.add_edge("shiro", "supervisor")
    g.add_edge("chlammy", "supervisor")
    g.add_conditional_edges("hitl", _route, {
        "shiro": "shiro",
        "supervisor": "supervisor",
        "fin": END,
    })

    return g.compile(checkpointer=WebCheckpointer())
