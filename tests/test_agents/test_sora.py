"""Pruebas de Sora."""
from agents.sora.agent import SoraStrategist


def test_plan_edge(tmp_edge):
    sora = SoraStrategist(edge_id=tmp_edge["edge_id"])
    plan = sora.plan_edge(tmp_edge["edge_id"], "Idea semilla")
    assert len(plan["objetivos"]) >= 1
    assert len(plan["entregables"]) >= 1
    assert plan["avance"] == 0


def test_execute_updates_state(tmp_edge):
    sora = SoraStrategist(edge_id=tmp_edge["edge_id"])
    state = {"edge_id": tmp_edge["edge_id"], "seed": "Idea"}
    state = sora.execute(state)
    assert state["current_step"] == "supervisor"
    assert "objetivos" in state
