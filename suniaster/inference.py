"""Invocación opt-in de modelos Suniaster con filtrado y metadatos."""
from __future__ import annotations

import os
from typing import Any

from privacy.filters import filter_prompt_external, is_safe


class ModelUnavailable(RuntimeError):
    """No se pudo completar una inferencia con los proveedores autorizados."""


def invoke_agent(agent: str, prompt: str) -> dict[str, str] | None:
    """Invoca el modelo asignado si Tet habilitó explícitamente modelos externos."""
    enabled = os.getenv("DISBOARD_USE_LLM", "auto").strip().lower()
    if enabled not in {"1", "true", "yes", "on"}:
        if enabled != "auto" or not any(
            os.getenv(name)
            for name in ("GROQ_API_KEY", "GOOGLE_AI_STUDIO_API_KEY", "OLLAMA_BASE_URL")
        ):
            return None

    filtered_prompt = filter_prompt_external(prompt)
    if not is_safe(filtered_prompt):
        raise ValueError("El filtro no pudo garantizar que el prompt esté libre de datos conocidos.")

    from suniaster.router import SuniasterRouter

    try:
        router = SuniasterRouter()
        response, provenance = router.invoke_for(agent, filtered_prompt)
    except Exception as error:
        raise ModelUnavailable(
            f"Inferencia no disponible para {agent} ({type(error).__name__})."
        ) from error
    content: Any = getattr(response, "content", response)
    if isinstance(content, list):
        content = "\n".join(
            block["text"] for block in content
            if isinstance(block, dict) and isinstance(block.get("text"), str)
        )
    if not isinstance(content, str) or not content.strip():
        raise ValueError(f"El modelo de {agent} devolvió una respuesta vacía o no textual.")

    return {
        "text": content.strip(),
        **provenance,
    }