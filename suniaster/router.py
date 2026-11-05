"""Enrutador de Suniaster: decide qué proveedor/modelo usa cada agente.

Lee `suniaster/config.yaml`, respeta la política free/pago y devuelve un
modelo LangChain listo para invocar. Si el proveedor preferido falla,
intenta el fallback configurado.

Si falta WOLFRAM_API_KEY y el agente declara `tools: [wolfram]`, el router
asigna el fallback declarado en `defaults.wolfram_fallback_*` (por defecto
Google Gemini 2.5 Pro). Shiro declarará qué proveedor usó y Tet validará.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv

from suniaster.providers import ProviderUnavailable, create_model

load_dotenv()

CONFIG_PATH = Path(os.getenv("SUNIASTER_CONFIG", "suniaster/config.yaml"))

DEFAULT_AGENT_BY_KIND = {
    "planner": "sora",
    "executor": "shiro",
    "auditor": "chlammy",
    "researcher": "jibril",
    "orchestrator": "stephanie",
    "assistant": "fiel",
    "data": "izuna",
    "updater": "suniaster_updater",
}


class SuniasterRouter:
    """Asigna modelos a agentes según la configuración de Suniaster."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = Path(config_path) if config_path else CONFIG_PATH
        self.config = self._load_config()

    # ------------------------------------------------------------------ #
    # Configuración
    # ------------------------------------------------------------------ #
    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"No se encontró {self.config_path}")
        return yaml.safe_load(self.config_path.read_text(encoding="utf-8"))

    def _policy(self) -> Dict[str, Any]:
        return self.config.get("defaults", {})

    # ------------------------------------------------------------------ #
    # Asignación
    # ------------------------------------------------------------------ #
    def get_model_for(self, agent: str) -> Any:
        agents = self.config.get("agents", {})
        if agent not in agents:
            raise KeyError(f"Agente no configurado en Suniaster: {agent}")

        entry = agents[agent]
        provider = entry["provider"]
        model = entry["model"]

        # Fallback por falta de WOLFRAM_API_KEY
        if "wolfram" in entry.get("tools", []) and not os.getenv("WOLFRAM_API_KEY"):
            provider = self._policy().get("wolfram_fallback_provider", "google")
            model = self._policy().get("wolfram_fallback_model", "gemini-2.5-pro")

        # Política free/pago
        if not self._policy().get("allow_paid", False):
            provider_conf = self.config["providers"].get(provider, {})
            if not provider_conf.get("free_tier", False):
                fallback_provider = self._policy().get("fallback_free", "groq")
                return self._try(agent, fallback_provider, None)

        return self._try(agent, provider, model)

    def _try(self, agent: str, provider: str, model: Optional[str]) -> Any:
        try:
            return create_model(provider, model or self._model_or_default(provider))
        except (ProviderUnavailable, ValueError) as e:
            entry = self.config["agents"][agent]
            fb_provider = entry.get("fallback_provider")
            fb_model = entry.get("fallback_model")
            if fb_provider and fb_provider != provider:
                return self._try(agent, fb_provider, fb_model)
            raise e

    def _model_or_default(self, provider: str) -> str:
        conf = self.config["providers"].get(provider, {})
        models = conf.get("models", [])
        if not models:
            raise ValueError(f"Proveedor {provider} sin modelos configurados.")
        return models[0]

    # ------------------------------------------------------------------ #
    # Metadatos
    # ------------------------------------------------------------------ #
    def describe_agent(self, agent: str) -> Dict[str, Any]:
        entry = self.config.get("agents", {}).get(agent, {})
        return {
            "agent": agent,
            "provider": entry.get("provider"),
            "model": entry.get("model"),
            "fallback_provider": entry.get("fallback_provider"),
            "fallback_model": entry.get("fallback_model"),
            "tools": list(entry.get("tools", [])),
            "role": entry.get("role", ""),
        }

    def agent_tools(self, agent: str) -> List[str]:
        return list(self.config.get("agents", {}).get(agent, {}).get("tools", []))

    def default_agent_for(self, kind: str) -> str:
        if kind not in DEFAULT_AGENT_BY_KIND:
            raise KeyError(f"Kind no soportado: {kind}")
        return DEFAULT_AGENT_BY_KIND[kind]
