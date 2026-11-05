"""Pruebas del grafo web (LangGraph)."""
from __future__ import annotations

import pytest


def test_dashboard_creates_and_displays_edge(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    import web.server as server

    monkeypatch.setattr("core.edge.EDGES_ROOT", tmp_path / "edges")
    registered = []

    class Registry:
        def registrar(self, edge):
            registered.append(edge.id)

    monkeypatch.setattr(server, "ElkiaRegistry", Registry)
    client = TestClient(server.app, client=("127.0.0.1", 8000))

    assert client.get("/edges/new").status_code == 200
    response = client.post("/edges/new", json={"title": "Dashboard flow"})
    assert response.status_code == 200
    edge_id = response.json()["edge_id"]
    assert registered == [edge_id]

    detail = client.get(f"/edges/{edge_id}")
    assert detail.status_code == 200
    assert "Dashboard flow" in detail.text


def test_artifact_api_lists_and_verifies_registered_files(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from core.artifact import Artifact
    from core.edge import Edge
    from web.server import app

    monkeypatch.setattr("core.edge.EDGES_ROOT", tmp_path / "edges")
    edge = Edge.crear_desde_semilla(None, titulo="Artifact test")
    source = tmp_path / "result.txt"
    source.write_text("verified artifact", encoding="utf-8")
    artifact = Artifact.register(edge, source, agent="Shiro")
    client = TestClient(app, client=("127.0.0.1", 8000))

    response = client.get("/api/artifacts", params={"project": edge.id})
    assert response.status_code == 200
    assert response.json()["artifacts"][0]["sha256"] == artifact.sha256

    response = client.get(f"/artifacts/{edge.id}/{artifact.name}")
    assert response.status_code == 200
    assert "verified artifact" in response.text

    artifact.path.write_text("altered artifact", encoding="utf-8")
    response = client.get(f"/artifacts/{edge.id}/{artifact.name}")
    assert response.status_code == 409


def test_artifact_register_rejects_path_traversal(tmp_path):
    from core.artifact import Artifact
    from core.edge import Edge

    edge = Edge.crear_desde_semilla(None, titulo="Traversal test", ruta_edges=tmp_path / "edges")
    source = tmp_path / "result.txt"
    source.write_text("artifact", encoding="utf-8")

    with pytest.raises(ValueError):
        Artifact.register(edge, source, agent="Shiro", target_relative="../outside.txt")


def test_artifact_registration_does_not_overwrite_audited_file(tmp_path):
    from core.artifact import Artifact
    from core.edge import Edge

    edge = Edge.crear_desde_semilla(None, titulo="Immutable artifacts", ruta_edges=tmp_path / "edges")
    first_source = tmp_path / "first.txt"
    first_source.write_text("version one", encoding="utf-8")
    second_source = tmp_path / "second.txt"
    second_source.write_text("version two", encoding="utf-8")

    first = Artifact.register(edge, first_source, agent="Tet", target_relative="result.txt")
    second = Artifact.register(edge, second_source, agent="Tet", target_relative="result.txt")

    assert first.name == "result.txt"
    assert second.name == "result-2.txt"
    assert first.path.read_text(encoding="utf-8") == "version one"
    assert second.path.read_text(encoding="utf-8") == "version two"


def test_graph_runs_with_persistent_checkpointer(tmp_path, monkeypatch):
    from web.graph import build_graph

    monkeypatch.setenv("DISBOARD_WEB_CHECKPOINT_DB", str(tmp_path / "checkpoints.sqlite"))
    g = build_graph()
    result = g.invoke(
        {"edge_id": "edge-test", "objetivos": ["test"], "entregables": []},
        config={"configurable": {"thread_id": "edge-test"}},
    )

    assert result["current_step"] == "supervisor"
    assert result["next_agent"] == "hitl"


def test_langgraph_api_pauses_and_resumes_with_human_verdict(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    import web.server as server
    from web.graph import build_graph

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TET_SIGNING_KEY", "graph-test-key-" + "x" * 32)
    monkeypatch.setenv("DISBOARD_WEB_CHECKPOINT_DB", str(tmp_path / "graph.sqlite"))
    monkeypatch.setattr(server, "_graph", build_graph())
    client = TestClient(server.app, client=("127.0.0.1", 8000))

    started = client.post(
        "/api/graph/runs",
        json={"edge_id": "edge-graph-test", "seed": "Ejecutar el flujo LangGraph."},
    )
    assert started.status_code == 200, started.text
    assert started.json()["state"]["__interrupt__"]

    resumed = client.post(
        "/api/verdict",
        json={"edge_id": "edge-graph-test", "verdict": "approve"},
    )
    assert resumed.status_code == 200, resumed.text
    assert resumed.json()["state"]["current_step"] == "fin"
