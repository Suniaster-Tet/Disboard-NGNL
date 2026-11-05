"""Pruebas de Shiro."""
import json

from agents.shiro.agent import ShiroAnalyst
from agents.shiro.antigravity_client import AntigravityClient
from agents.shiro.wolfram_client import WolframClient


def test_tdd_generates_code_and_test():
    shiro = ShiroAnalyst(edge_id="edge-test")
    code, test_code = shiro.generate_tdd_code("spec")
    assert "def solve_algorithm" in code
    assert "class TestApprovedSpecification" in test_code
    assert "NotImplementedError" in code
    assert shiro._generation_metadata["mode"] == "scaffold_fallback"


def test_tdd_uses_model_and_records_scientific_context(monkeypatch):
    captured = {}
    model_output = {
        "code": "def solve_algorithm(value):\n    return value * 2\n",
        "test": "def test_solve_algorithm():\n    assert solve_algorithm(2) == 4\n",
    }

    def fake_invoke(agent, prompt):
        captured["agent"] = agent
        captured["prompt"] = prompt
        return {"text": json.dumps(model_output), "provider": "Groq", "model": "free-model"}

    monkeypatch.setattr("agents.shiro.agent.invoke_agent", fake_invoke)
    shiro = ShiroAnalyst()
    code, test_code = shiro.generate_tdd_code(
        "Duplicar un valor de entrada.",
        bibliography=[{"doi": "10.1234/approved", "title": "Método"}],
        theories=["Aritmética definida por Tet"],
    )

    assert code == model_output["code"]
    assert test_code == model_output["test"]
    assert captured["agent"] == "shiro"
    assert "10.1234/approved" in captured["prompt"]
    assert "Aritmética definida por Tet" in captured["prompt"]
    assert shiro._generation_metadata["provider"] == "Groq"


def test_model_code_cannot_introduce_unapproved_doi(monkeypatch):
    output = {
        "code": "# DOI 10.9999/inventado\ndef solve_algorithm():\n    return None\n",
        "test": "def test_solve_algorithm():\n    assert solve_algorithm() is None\n",
    }
    monkeypatch.setattr(
        "agents.shiro.agent.invoke_agent",
        lambda agent, prompt: {"text": json.dumps(output), "provider": "groq", "model": "test"},
    )
    shiro = ShiroAnalyst()
    code, _ = shiro.generate_tdd_code(
        "Implementar", bibliography=[{"doi": "10.1234/approved"}]
    )

    assert "10.9999/inventado" not in code
    assert shiro._generation_metadata["mode"] == "scaffold_fallback"


def test_wolfram_without_key_returns_mock(monkeypatch):
    monkeypatch.delenv("WOLFRAM_API_KEY", raising=False)
    res = WolframClient().evaluate_expression("x+1")
    assert res["status"] == "mock"


def test_antigravity_available(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/agy")
    assert AntigravityClient().is_available()
