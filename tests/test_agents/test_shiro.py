"""Pruebas de Shiro."""
from agents.shiro.agent import ShiroAnalyst
from agents.shiro.antigravity_client import AntigravityClient
from agents.shiro.wolfram_client import WolframClient


def test_tdd_generates_code_and_test():
    code, test_code = ShiroAnalyst(edge_id="edge-test").generate_tdd_code("spec")
    assert "def solve_algorithm" in code
    assert "class TestShiroLogic" in test_code


def test_wolfram_without_key_returns_mock(monkeypatch):
    monkeypatch.delenv("WOLFRAM_API_KEY", raising=False)
    res = WolframClient().evaluate_expression("x+1")
    assert res["status"] == "mock"


def test_antigravity_available(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/agy")
    assert AntigravityClient().is_available()
