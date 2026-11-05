"""Pruebas de Elkia (registro, reglas, estado, dashboard)."""
from __future__ import annotations

from pathlib import Path

from core.contract import Contract
from core.edge import Edge
from elkia.dashboard import EdgePriority, ElkiaDashboard
from elkia.registry import ElkiaRegistry
from elkia.rules import BoardRules
from elkia.state import EdgeState


def test_registry_register_and_list(tmp_path, monkeypatch, tmp_edge):
    monkeypatch.setattr("core.edge.EDGES_ROOT", tmp_path / "edges")
    ruta = tmp_path / "elkia_registry.json"
    registry = ElkiaRegistry(ruta=ruta)
    edge = Edge.cargar(tmp_edge["edge_id"])
    registry.registrar(edge)
    assert registry.existe(edge.id)
    assert len(registry.listar()) == 1


def test_state_limits_progress():
    state = EdgeState(avance=150)
    assert state.avance == 100
    state = EdgeState(avance=-10)
    assert state.avance == 0


def test_dashboard_priority_by_days():
    assert ElkiaDashboard.compute_priority(2) == EdgePriority.CRITICA
    assert ElkiaDashboard.compute_priority(5) == EdgePriority.ALTA
    assert ElkiaDashboard.compute_priority(10) == EdgePriority.MEDIA
    assert ElkiaDashboard.compute_priority(30) == EdgePriority.BAJA
    assert ElkiaDashboard.compute_priority(None) == EdgePriority.BAJA


def test_dashboard_render_empty():
    dashboard = ElkiaDashboard(registro=ElkiaRegistry(ruta=Path("/tmp/no-existe.json")))
    texto = dashboard.render_markdown(termometros=[])
    assert "Sin edges activos" in texto


def test_rules_validate_execution_without_contract(tmp_edge):
    edge = Edge.cargar(tmp_edge["edge_id"])
    contract = Contract(edge_id=edge.id)
    errors = BoardRules.validar_ejecucion(edge, contract)
    assert any("no ha sido aprobado" in e for e in errors)
