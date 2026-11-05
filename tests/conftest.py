"""Fixtures compartidas para la suite de Disboard-NGNL."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def tmp_edge(tmp_path: Path) -> dict:
    """Crea un edge temporal con contrato, log y artefactos."""
    edge_dir = tmp_path / "edges" / "edge-test"
    (edge_dir / "artifacts").mkdir(parents=True)
    (edge_dir / "out").mkdir()
    edge_meta = {
        "id": "edge-test",
        "titulo": "Edge de prueba",
        "ruta": str(edge_dir),
        "avance": 0,
        "prioridad": "media",
        "estado": "NUEVO",
        "creado_en": "2026-01-01T00:00:00+00:00",
    }
    (edge_dir / "edge.json").write_text(json.dumps(edge_meta), encoding="utf-8")
    (edge_dir / "contract.md").write_text(
        "# Contrato del edge `edge-test`\n\n"
        "## Objetivos\n- Objetivo de prueba\n\n"
        "## Metas\n- Meta de prueba\n\n"
        "## Entregables\n- `E1` — Entregable de prueba\n",
        encoding="utf-8",
    )
    (edge_dir / "log.jsonl").touch()
    return {"edge_id": "edge-test", "ruta": edge_dir}


@pytest.fixture
def tmp_registry(tmp_path: Path) -> Path:
    """Crea un registro de Elkia vacío en un directorio temporal."""
    ruta = tmp_path / "edges" / "elkia_registry.json"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps({"edges": {}}), encoding="utf-8")
    return ruta


@pytest.fixture
def tmp_suniaster_config(tmp_path: Path) -> Path:
    """Configuración mínima de Suniaster para tests."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "defaults:\n"
        "  allow_paid: false\n"
        "  fallback_free: groq\n"
        "agents:\n"
        "  sora:\n"
        "    provider: groq\n"
        "    model: llama-3.3-70b-versatile\n"
        "    fallback_provider: google\n"
        "    fallback_model: gemini-2.5-flash\n"
        "providers:\n"
        "  groq:\n"
        "    type: groq\n"
        "    free_tier: true\n"
        "    env_key: GROQ_API_KEY\n"
        "    models:\n"
        "      - llama-3.3-70b-versatile\n"
        "  google:\n"
        "    type: google_genai\n"
        "    free_tier: true\n"
        "    env_key: GOOGLE_AI_STUDIO_API_KEY\n"
        "    models:\n"
        "      - gemini-2.5-flash\n",
        encoding="utf-8",
    )
    return cfg
