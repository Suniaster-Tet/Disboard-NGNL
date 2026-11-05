"""Pruebas de Sora."""
import json

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


def test_plan_uses_approved_references_and_tet_theories(monkeypatch):
    captured = {}
    model_output = {
        "objetivos": ["Evaluar reproducibilidad"],
        "metas": ["Comparar métodos"],
        "entregables": [
            {"id": "E1", "descripcion": "Definir el plan", "agente_asignado": "Sora"},
            {"id": "E2", "descripcion": "Preparar código reproducible", "agente_asignado": "Shiro"},
        ],
    }

    def fake_invoke(agent, prompt):
        captured["agent"] = agent
        captured["prompt"] = prompt
        return {"text": json.dumps(model_output), "provider": "Groq", "model": "free-model"}

    monkeypatch.setattr("agents.sora.agent.invoke_agent", fake_invoke)
    plan = SoraStrategist().plan_edge(
        "edge-test",
        "Analizar redes con ana@example.org",
        bibliography=[{"doi": "10.1234/approved", "title": "Paper revisado"}],
        theories=["Teoría de grafos definida por Tet"],
    )

    assert captured["agent"] == "sora"
    assert "10.1234/approved" in captured["prompt"]
    assert "Teoría de grafos definida por Tet" in captured["prompt"]
    assert plan["objetivos"] == ["Evaluar reproducibilidad"]
    assert plan["model_provenance"]["model"] == "free-model"


def test_invalid_model_plan_uses_audited_template_fallback(monkeypatch):
    monkeypatch.setattr(
        "agents.sora.agent.invoke_agent",
        lambda agent, prompt: {"text": "not json", "provider": "Groq", "model": "free-model"},
    )
    plan = SoraStrategist().plan_edge("edge-test", "Solicitud")
    assert plan["objetivos"]
    assert plan["model_provenance"]["mode"] == "deterministic_fallback"


def test_model_plan_cannot_introduce_unapproved_doi(monkeypatch):
    import json

    output = {
        "objetivos": ["Usar 10.9999/inventado"],
        "metas": ["Meta"],
        "entregables": [
            {"id": "E1", "descripcion": "Plan", "agente_asignado": "Sora"}
        ],
    }
    monkeypatch.setattr(
        "agents.sora.agent.invoke_agent",
        lambda agent, prompt: {"text": json.dumps(output), "provider": "groq", "model": "test"},
    )

    plan = SoraStrategist().plan_edge("edge-test", "Solicitud")
    assert plan["model_provenance"]["mode"] == "deterministic_fallback"
    assert "10.9999/inventado" not in " ".join(plan["objetivos"])
