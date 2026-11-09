#!/usr/bin/env python3
"""Chequeo de entorno de Disboard-NGNL (Elkia / Suniaster).

Verifica:
- Python y dependencias críticas.
- Clave de firma de aprobaciones y variables opcionales.
- Disponibilidad de adaptadores configurados (no hace llamadas de inferencia).
- Estado de Suniaster (modelos por agente).
- Estado de Elkia (registro de edges).
- Configuración presente (`suniaster/config.yaml`, `config/apis.yaml`).

Uso:
    python scripts/healthcheck.py
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _check_python() -> tuple[bool, str]:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    ok = sys.version_info >= (3, 11)
    return ok, f"Python {version}"


def _check_dependencies() -> list[tuple[bool, str]]:
    checks: list[tuple[bool, str]] = []
    for module, name in [
        ("langgraph", "LangGraph"),
        ("fastapi", "FastAPI"),
        ("polars", "Polars"),
        ("pandas", "Pandas"),
        ("duckdb", "DuckDB"),
        ("jinja2", "Jinja2"),
        ("pypdf", "pypdf"),
        ("yaml", "PyYAML"),
    ]:
        try:
            __import__(module)
            checks.append((True, f"{name} disponible"))
        except ImportError:
            checks.append((False, f"{name} NO disponible"))
    return checks


def _check_env() -> list[tuple[bool, str]]:
    checks: list[tuple[bool, str]] = []

    required = {
        "TET_SIGNING_KEY": "Firma HITL de Tet",
    }
    for var, desc in required.items():
        value = os.getenv(var, "")
        if len(value.encode("utf-8")) >= 32:
            checks.append((True, f"{var} configurada ({desc})"))
        elif value:
            checks.append((False, f"{var} es débil; requiere al menos 32 bytes aleatorios."))
        else:
            checks.append((False, f"{var} FALTA ({desc})"))

    optional = {
        "GROQ_API_KEY": "Groq, proveedor de modelos",
        "GOOGLE_AI_STUDIO_API_KEY": "Google AI Studio, proveedor de modelos",
        "WOLFRAM_API_KEY": "Wolfram para Shiro",
        "CROSSREF_MAILTO": "Crossref polite pool para Jibril",
        "OPENALEX_API_KEY": "OpenAlex para Jibril",
    }
    for var, desc in optional.items():
        if os.getenv(var):
            checks.append((True, f"{var} configurada ({desc})"))
        else:
            checks.append((True, f"{var} no configurada (opcional; {desc})"))
    return checks


def _check_tools() -> list[tuple[bool, str]]:
    checks: list[tuple[bool, str]] = []
    for binary, name in [
        ("latexmk", "LaTeX (latexmk)"),
        ("libreoffice", "LibreOffice"),
        ("agy", "Antigravity CLI (opcional)"),
        ("cloudflared", "cloudflared (opcional; acceso remoto)"),
    ]:
        if shutil.which(binary):
            checks.append((True, f"{name} disponible"))
        else:
            checks.append((True, f"{name} no disponible (opcional)"))
    return checks


def _check_config() -> list[tuple[bool, str]]:
    checks: list[tuple[bool, str]] = []
    for path, desc in [
        ("suniaster/config.yaml", "Configuración de Suniaster"),
        ("config/apis.yaml", "Configuración de APIs externas"),
        ("config/logging.yaml", "Configuración de logging"),
    ]:
        if Path(path).exists():
            checks.append((True, f"{desc} presente"))
        else:
            checks.append((False, f"{desc} FALTA ({path})"))
    return checks


def _check_suniaster() -> list[tuple[bool, str]]:
    checks: list[tuple[bool, str]] = []
    llm_setting = os.getenv("DISBOARD_USE_LLM", "auto").strip().lower()
    llm_enabled = llm_setting in {"1", "true", "yes", "on"} or (
        llm_setting == "auto"
        and any(
            os.getenv(name)
            for name in (
                "GROQ_API_KEY",
                "GOOGLE_AI_STUDIO_API_KEY",
                "OLLAMA_BASE_URL",
            )
        )
    )
    try:
        from suniaster.updater import SuniasterUpdater
        result = SuniasterUpdater().check_and_update()
        if result["status"] == "ok":
            checks.append((True, f"Suniaster OK ({len(result['details'])} agentes)"))
        else:
            checks.append((
                not llm_enabled,
                f"Suniaster degradado ({result['agents_with_error']} adaptadores no disponibles)"
                + ("; LLM desactivado, se usarán fallbacks locales." if not llm_enabled else ""),
            ))
            for agent, det in result["details"].items():
                if not det.get("ok"):
                    error_type = det.get("error", "error").split(":", 1)[0]
                    checks.append((not llm_enabled, f"  - {agent}: {error_type}"))
    except Exception as e:
        checks.append((not llm_enabled, f"Suniaster no disponible ({type(e).__name__})"))
    return checks


def _check_elkia() -> list[tuple[bool, str]]:
    checks: list[tuple[bool, str]] = []
    try:
        from elkia.registry import ElkiaRegistry
        registry = ElkiaRegistry()
        edges = registry.listar()
        checks.append((True, f"Elkia OK ({len(edges)} edge(s) registrado(s))"))
    except Exception as e:
        checks.append((False, f"Elkia no disponible: {e}"))
    return checks


def main() -> int:
    print("✦ [Disboard-NGNL]: Healthcheck\n")

    sections = [
        ("Python", [_check_python()]),
        ("Dependencias", _check_dependencies()),
        ("Variables de entorno", _check_env()),
        ("Herramientas del sistema", _check_tools()),
        ("Configuración", _check_config()),
        ("Suniaster", _check_suniaster()),
        ("Elkia", _check_elkia()),
    ]

    failures = 0
    for title, checks in sections:
        print(f"## {title}")
        for ok, message in checks:
            icon = "✔" if ok else "✖"
            print(f"  {icon} {message}")
            if not ok:
                failures += 1
        print()

    if failures:
        print(f"✖ Healthcheck con {failures} problema(s). Revisa los mensajes anteriores.")
        return 1
    print("✔ Healthcheck básico OK. Verifica los servicios opcionales antes de necesitarlos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
