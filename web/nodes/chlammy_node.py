"""Nodo Chlammy: auditoría."""
from __future__ import annotations

from agents.chlammy.agent import ChlammyAuditor
from core.state_schema import OverallState


def chlammy_node(state: OverallState) -> OverallState:
    edge_id = state.get("edge_id", "edge-default")
    chlammy = ChlammyAuditor(edge_id=edge_id)

    contract = state.get("action_details", {}).get("contract", {})
    deliverables = state.get("artifacts", [])

    result = chlammy.verify_contract_alignment(contract, deliverables)
    state.setdefault("action_details", {})["audit"] = result
    state["current_step"] = "chlammy"
    state["next_agent"] = "hitl"
    return state
