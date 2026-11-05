"""Pruebas de Stephanie Dola."""
from agents.dola.agent import StephanieOrchestrator


def test_free_route_proceeds():
    d = StephanieOrchestrator(edge_id="edge-test", config={})
    res = d.route_agent_task("Sora", {"provider": "groq"})
    assert res["status"] == "proceed"


def test_paid_route_requires_confirmation():
    d = StephanieOrchestrator(edge_id="edge-test",
                              config={"confirm_before_paid_fallback": True})
    res = d.route_agent_task("Shiro", {"provider": "anthropic"})
    assert res["status"] == "interrupt_required"


def test_rollback():
    d = StephanieOrchestrator(edge_id="edge-test", config={})
    res = d.execute_rollback("edge-test", "Tet rechazó")
    assert res["status"] == "rollback_completed"
