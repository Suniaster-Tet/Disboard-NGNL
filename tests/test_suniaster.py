"""Pruebas de Suniaster (enrutador, proveedores, actualizador)."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from suniaster.providers import ProviderUnavailable, create_model
from suniaster.router import SuniasterRouter


def test_router_loads_config(tmp_suniaster_config):
    router = SuniasterRouter(config_path=tmp_suniaster_config)
    assert "sora" in router.config["agents"]


def test_router_unknown_agent(tmp_suniaster_config):
    router = SuniasterRouter(config_path=tmp_suniaster_config)
    with pytest.raises(KeyError):
        router.get_model_for("inexistente")


def test_router_respects_free_tier(tmp_suniaster_config, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "fake")
    router = SuniasterRouter(config_path=tmp_suniaster_config)
    with patch("suniaster.router.create_model", return_value="modelo-fake"):
        model = router.get_model_for("sora")
        assert model == "modelo-fake"


def test_router_maps_google_alias_to_langchain_adapter(tmp_suniaster_config, monkeypatch):
    monkeypatch.setenv("GOOGLE_AI_STUDIO_API_KEY", "fake-google-key")
    router = SuniasterRouter(config_path=tmp_suniaster_config)
    with patch("suniaster.router.create_model", return_value="google-model") as create:
        assert router._try("sora", "google", "gemini-2.5-flash") == "google-model"
    create.assert_called_once_with("google_genai", "gemini-2.5-flash")


def test_provider_not_supported():
    with pytest.raises(ValueError):
        create_model("inexistente", "modelo")


def test_provider_without_env(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ProviderUnavailable):
        create_model("groq", "llama-3.3-70b-versatile")


def test_router_falls_back_to_free_provider_after_invoke_error(tmp_suniaster_config, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "fake-groq-key")
    monkeypatch.setenv("GOOGLE_AI_STUDIO_API_KEY", "fake-google-key")

    class Model:
        def __init__(self, fails):
            self.fails = fails

        def invoke(self, prompt):
            if self.fails:
                raise RuntimeError("free tier quota exhausted")
            return "Gemini answer"

    def create(provider, model):
        return Model(fails=provider == "groq")

    router = SuniasterRouter(config_path=tmp_suniaster_config)
    with patch("suniaster.router.create_model", side_effect=create) as factory:
        response, provenance = router.invoke_for("sora", "prompt")

    assert response == "Gemini answer"
    assert provenance["provider"] == "google"
    assert [call.args[0] for call in factory.call_args_list] == ["groq", "google_genai"]


def test_inference_filters_prompt_before_model_call(monkeypatch):
    from types import SimpleNamespace

    from suniaster.inference import invoke_agent

    monkeypatch.setenv("DISBOARD_USE_LLM", "true")
    captured = {}

    class Router:
        def invoke_for(self, agent, prompt):
            captured["agent"] = agent
            captured["prompt"] = prompt
            return SimpleNamespace(content="Model response"), {
                "provider": "groq", "model": "free-model", "agent": agent
            }

    monkeypatch.setattr("suniaster.router.SuniasterRouter", Router)
    result = invoke_agent("sora", "Contact ana@example.org about the research.")

    assert "ana@example.org" not in captured["prompt"]
    assert "[EMAIL_PROTECTED]" in captured["prompt"]
    assert result["provider"] == "groq"
