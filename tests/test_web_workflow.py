"""Pruebas del flujo HITL operativo del dashboard."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from core.edge import Edge
from web.workflow import EdgeWorkflow


class EmptyRegistry:
    def existe(self, edge_id: str) -> bool:
        return False


def create_workflow(tmp_path, monkeypatch) -> EdgeWorkflow:
    monkeypatch.setenv("TET_SIGNING_KEY", "workflow-test-key-" + "x" * 32)
    monkeypatch.setattr("web.workflow.ElkiaRegistry", EmptyRegistry)
    edge = Edge.crear_desde_semilla(
        None,
        titulo="Flujo de prueba",
        ruta_edges=tmp_path / "edges",
    )
    return EdgeWorkflow(edge)


def test_full_hitl_workflow_uses_only_tet_approved_references(tmp_path, monkeypatch):
    workflow = create_workflow(tmp_path, monkeypatch)
    workflow.add_request("Analizar la reproducibilidad de algoritmos.")
    workflow.add_reference(
        "10.1234/example",
        {"doi": "10.1234/example", "title": "Referencia verificada", "authors": ["A. Autor"]},
        proposer="Tet",
    )

    unapproved_plan = workflow.generate_plan()
    assert unapproved_plan["plan"]["bibliography"] == []

    workflow.review_reference("10.1234/example", "approve")
    plan = workflow.generate_plan()
    assert plan["plan"]["bibliography"][0]["doi"] == "10.1234/example"
    workflow.approve_plan()
    assert workflow.snapshot()["deliverables"][0]["estado"] == "aprobado"

    for deliverable_id in ("E2", "E3", "E4"):
        workflow.execute_deliverable(deliverable_id)
        workflow.review_deliverable(deliverable_id, "approve")

    final = workflow.decide_final("approve")
    assert final["final"]["status"] == "approved"
    edge = Edge.cargar(workflow.edge.id, ruta_edges=tmp_path / "edges")
    assert edge.estado == "COMPLETO"
    assert edge.avance == 100


def test_rejecting_deliverable_rolls_back_its_artifacts(tmp_path, monkeypatch):
    workflow = create_workflow(tmp_path, monkeypatch)
    workflow.add_request("Crear un cálculo reproducible.")
    workflow.generate_plan()
    workflow.approve_plan()

    workflow.execute_deliverable("E3")
    records = workflow.snapshot()["artifacts"]["E3"]
    assert all(__import__("pathlib").Path(record["path"]).is_file() for record in records)

    workflow.review_deliverable("E3", "reject", "El enfoque no corresponde.")
    assert all(not __import__("pathlib").Path(record["path"]).exists() for record in records)
    events = [json.loads(line) for line in workflow.edge.ruta_log.read_text().splitlines()]
    assert any(event["evento"] == "artifact_deleted" for event in events)


def test_tampered_final_signature_is_not_accepted(tmp_path, monkeypatch):
    workflow = create_workflow(tmp_path, monkeypatch)
    workflow.add_request("Completar un flujo con cierre firmado.")
    workflow.add_reference(
        "10.1234/closure",
        {"doi": "10.1234/closure", "title": "Cierre verificable", "authors": ["Tet"]},
        proposer="Tet",
    )
    workflow.review_reference("10.1234/closure", "approve")
    workflow.generate_plan()
    workflow.approve_plan()
    for deliverable_id in ("E2", "E3", "E4"):
        workflow.execute_deliverable(deliverable_id)
        workflow.review_deliverable(deliverable_id, "approve")
    workflow.decide_final("approve")

    persisted = json.loads(workflow.path.read_text(encoding="utf-8"))
    persisted["final"]["approval"]["firma"] = "0" * 64
    workflow.path.write_text(json.dumps(persisted), encoding="utf-8")

    reopened = EdgeWorkflow(Edge.cargar(workflow.edge.id, ruta_edges=tmp_path / "edges"))
    assert reopened.snapshot()["final"]["status"] == "invalid"
    reopened._refresh_edge()
    assert reopened.edge.estado != "COMPLETO"


def test_final_approval_refuses_artifact_changed_after_review(tmp_path, monkeypatch):
    workflow = create_workflow(tmp_path, monkeypatch)
    workflow.add_request("Crear un cálculo seguro.")
    workflow.add_reference(
        "10.1234/secure",
        {"doi": "10.1234/secure", "title": "Referencia", "authors": []},
        proposer="Tet",
    )
    workflow.review_reference("10.1234/secure", "approve")
    workflow.generate_plan()
    workflow.approve_plan()

    for deliverable_id in ("E2", "E3", "E4"):
        workflow.execute_deliverable(deliverable_id)
        workflow.review_deliverable(deliverable_id, "approve")

    artifact = workflow.state["artifacts"]["E3"][0]
    Path(artifact["path"]).write_text("alterado después de la aprobación", encoding="utf-8")

    with pytest.raises(ValueError, match="hash"):
        workflow.decide_final("approve")


def test_plan_cannot_be_approved_without_signing_key(tmp_path, monkeypatch):
    workflow = create_workflow(tmp_path, monkeypatch)
    workflow.add_request("Solicitud sin clave.")
    workflow.generate_plan()
    monkeypatch.delenv("TET_SIGNING_KEY")

    with pytest.raises(RuntimeError, match="TET_SIGNING_KEY"):
        workflow.approve_plan()


def test_http_flow_from_direct_request_to_final_approval(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    import web.server as server
    from elkia.registry import ElkiaRegistry

    monkeypatch.setenv("TET_SIGNING_KEY", "http-workflow-test-key-" + "x" * 32)
    monkeypatch.setattr("core.edge.EDGES_ROOT", tmp_path / "edges")
    registry = ElkiaRegistry(ruta=tmp_path / "edges" / "elkia_registry.json")
    monkeypatch.setattr(server, "ElkiaRegistry", lambda: registry)
    monkeypatch.setattr("web.workflow.ElkiaRegistry", lambda: registry)
    monkeypatch.setattr(
        server.JibrilScientific,
        "search_references",
        lambda self, query, limit: [{
            "doi": "10.1234/http-flow", "title": "HTTP reference", "authors": ["Tet"],
            "year": 2026, "journal": "Tests", "source": "crossref_search",
        }],
    )
    client = TestClient(server.app, client=("127.0.0.1", 8000))

    response = client.post("/api/requests", json={"text": "Investigar desde el dashboard."})
    assert response.status_code == 200
    edge_id = response.json()["edge_id"]

    suggestions = client.post(
        f"/api/edges/{edge_id}/bibliography/search",
        json={"query": "reproducibilidad"},
    )
    assert suggestions.status_code == 200
    approved_reference = client.post(
        f"/api/edges/{edge_id}/bibliography/10.1234/http-flow/decision",
        json={"verdict": "approve"},
    )
    assert approved_reference.status_code == 200

    plan = client.post(f"/api/edges/{edge_id}/plan")
    assert plan.json()["workflow"]["plan"]["bibliography"][0]["doi"] == "10.1234/http-flow"
    detail = client.get(f"/edges/{edge_id}")
    assert detail.status_code == 200
    assert "Plan de Sora" in detail.text
    assert "HTTP reference" in detail.text
    assert client.post(f"/api/edges/{edge_id}/plan/approve", json={}).status_code == 200

    for deliverable_id in ("E2", "E3", "E4"):
        executed = client.post(f"/api/edges/{edge_id}/deliverables/{deliverable_id}/execute")
        assert executed.status_code == 200, executed.text
        reviewed = client.post(
            f"/api/edges/{edge_id}/deliverables/{deliverable_id}/decision",
            json={"verdict": "approve"},
        )
        assert reviewed.status_code == 200, reviewed.text

    final = client.post(
        f"/api/edges/{edge_id}/final/decision",
        json={"verdict": "approve"},
    )
    assert final.status_code == 200
    assert final.json()["workflow"]["final"]["status"] == "approved"


def test_console_and_dashboard_share_persisted_workflow(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    import console.commands as console_commands
    import web.server as server
    from elkia.registry import ElkiaRegistry

    monkeypatch.setenv("TET_SIGNING_KEY", "shared-interface-key-" + "x" * 32)
    edges_root = tmp_path / "edges"
    monkeypatch.setattr("core.edge.EDGES_ROOT", edges_root)
    registry = ElkiaRegistry(ruta=edges_root / "elkia_registry.json")
    monkeypatch.setattr(console_commands, "ElkiaRegistry", lambda: registry)
    monkeypatch.setattr(server, "ElkiaRegistry", lambda: registry)
    monkeypatch.setattr("web.workflow.ElkiaRegistry", lambda: registry)
    seed = tmp_path / "seed.md"
    seed.write_text("Estudiar intercambio entre consola y dashboard.", encoding="utf-8")

    with patch.object(console_commands.Presentation, "ask_verdict", return_value="aprobar"):
        assert console_commands.start(seed, "Shared workflow") == 0

    edge_id = next(iter(registry.listar_meta()))
    response = TestClient(server.app, client=("127.0.0.1", 8000)).get(
        f"/api/edges/{edge_id}/workflow"
    )
    assert response.status_code == 200
    assert response.json()["plan_approved"] is True
    assert response.json()["requests"][0]["text"] == seed.read_text(encoding="utf-8")