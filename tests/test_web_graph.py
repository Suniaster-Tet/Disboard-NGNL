"""Pruebas del grafo web (LangGraph)."""
from __future__ import annotations

import pytest


def test_graph_placeholder():
    try:
        from web.graph import build_graph
    except ImportError:
        pytest.skip("web/graph.py no implementado")
    g = build_graph()
    assert g is not None
