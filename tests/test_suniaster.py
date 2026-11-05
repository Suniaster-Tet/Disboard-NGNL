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
    with patch("suniaster.providers.create_model", return_value="modelo-fake"):
        model = router.get_model_for("sora")
        assert model == "modelo-fake"


def test_provider_not_supported():
    with pytest.raises(ValueError):
        create_model("inexistente", "modelo")


def test_provider_without_env(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ProviderUnavailable):
        create_model("groq", "llama-3.3-70b-versatile")
