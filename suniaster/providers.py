"""Adaptadores LangChain por proveedor de IA.

Suniaster usa LangChain para abstraer los SDKs nativos. Cada proveedor
devuelve un `BaseChatModel` listo para invocar.
"""
from __future__ import annotations

import os
from typing import Any


class ProviderUnavailable(RuntimeError):
    """Se lanza cuando el proveedor no tiene credenciales configuradas."""


_SUPPORTED = {"groq", "google_genai", "ollama", "openai", "anthropic", "deepseek"}


def list_supported_providers() -> list[str]:
    return sorted(_SUPPORTED)


def create_model(provider: str, model: str, **kwargs: Any):
    """Crea un modelo LangChain para el proveedor indicado."""
    if provider == "groq":
        _req_env("GROQ_API_KEY")
        from langchain_groq import ChatGroq
        return ChatGroq(model=model, temperature=0, **kwargs)

    if provider == "google_genai":
        api_key = _req_env("GOOGLE_AI_STUDIO_API_KEY")
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model, temperature=0, api_key=api_key, **kwargs)

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return ChatOllama(model=model, base_url=base_url, temperature=0, **kwargs)

    if provider == "openai":
        _req_env("OPENAI_API_KEY")
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, temperature=0, **kwargs)

    if provider == "anthropic":
        _req_env("ANTHROPIC_API_KEY")
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, temperature=0, **kwargs)

    if provider == "deepseek":
        _req_env("DEEPSEEK_API_KEY")
        from langchain_deepseek import ChatDeepSeek
        return ChatDeepSeek(model=model, temperature=0, **kwargs)

    raise ValueError(f"Proveedor no soportado: {provider}")


def _req_env(nombre: str) -> str:
    value = os.getenv(nombre)
    if not value:
        raise ProviderUnavailable(
            f"Falta la variable de entorno {nombre}. Configúrala en .env."
        )
    return value
