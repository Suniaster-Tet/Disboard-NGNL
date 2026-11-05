"""Pruebas del núcleo compartido (core/)."""
from __future__ import annotations

import pytest

from core.contract import Contract
from core.edge import Edge
from core.hitl import generar_firma_tet, verificar_firma_tet
from core.log import Log


def test_edge_crear_desde_semilla(tmp_path, monkeypatch):
    monkeypatch.setattr("core.edge.EDGES_ROOT", tmp_path / "edges")
    seed = tmp_path / "idea.md"
    seed.write_text("# Idea\nContenido", encoding="utf-8")
    edge = Edge.crear_desde_semilla(seed)
    assert edge.id.startswith("edge-idea-")
    assert (edge.ruta / "seed.md").exists()
    assert (edge.ruta / "edge.json").exists()


def test_edge_cargar(tmp_edge):
    edge = Edge.cargar(tmp_edge["edge_id"])
    assert edge.id == "edge-test"
    assert edge.avance == 0


def test_log_registrar_y_leer(tmp_edge):
    log = Log(tmp_edge["edge_id"], ruta=tmp_edge["ruta"] / "log.jsonl")
    log.registrar("evento_test", {"k": "v"}, agente="Sora")
    entradas = log.leer()
    assert len(entradas) == 1
    assert entradas[0]["evento"] == "evento_test"
    assert entradas[0]["agente"] == "Sora"


def test_contract_aprobar_y_guardar(tmp_edge, tmp_path):
    edge = Edge.cargar(tmp_edge["edge_id"])
    contract = Contract.desde_plan_sora(edge, {
        "objetivos": ["Obj 1"], "metas": ["Meta 1"],
        "entregables": [{"id": "E1", "descripcion": "Ent 1"}],
    })
    contract.aprobar("firma-falsa")
    ruta = tmp_path / "contract.md"
    contract.guardar(ruta)
    texto = ruta.read_text(encoding="utf-8")
    assert "Aprobado por Tet: **sí**" in texto
    assert "Obj 1" in texto


def test_contract_persists_tet_theories_and_approved_bibliography(tmp_edge, tmp_path):
    edge = Edge.cargar(tmp_edge["edge_id"])
    contract = Contract.desde_plan_sora(
        edge,
        {
            "objetivos": ["Objetivo"],
            "metas": ["Meta"],
            "entregables": [{"id": "E1", "descripcion": "Plan"}],
            "theories": ["Teoría de grafos definida por Tet"],
            "bibliography": [
                {"doi": "10.1234/approved", "title": "Referencia aprobada", "year": 2026, "source": "crossref"}
            ],
        },
    )
    path = tmp_path / "contract.md"
    contract.guardar(path)

    loaded = Contract.cargar(path)
    assert loaded.theories == ["Teoría de grafos definida por Tet"]
    assert loaded.bibliography == [
        {"doi": "10.1234/approved", "title": "Referencia aprobada (2026)", "source": "crossref"}
    ]


def test_hitl_firma_ida_y_vuelta(monkeypatch):
    monkeypatch.setenv("TET_SIGNING_KEY", "clave-de-prueba-" + "x" * 32)
    payload = {"edge_id": "edge-test", "accion": "aprobar"}
    firma = generar_firma_tet(payload)
    assert verificar_firma_tet(payload, firma)
    assert not verificar_firma_tet(payload, "firma-incorrecta")


def test_hitl_sin_clave_falla(monkeypatch):
    monkeypatch.delenv("TET_SIGNING_KEY", raising=False)
    with pytest.raises(RuntimeError):
        generar_firma_tet({"x": 1})


def test_hitl_rechaza_clave_debil(monkeypatch):
    monkeypatch.setenv("TET_SIGNING_KEY", "debil")
    with pytest.raises(RuntimeError, match="32 bytes"):
        generar_firma_tet({"x": 1})
