"""Servidor web local (FastAPI) con API JSON y dashboard HTML."""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from core.artifact import Artifact
from core.edge import Edge
from elkia.dashboard import ElkiaDashboard
from elkia.registry import ElkiaRegistry
from suniaster.updater import SuniasterUpdater
from web.dashboard import views
from web.graph import build_graph

app = FastAPI(title="Disboard-NGNL", version="1.0.0")
_graph = build_graph()


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------
class RunRequest(BaseModel):
    edge_id: str
    seed: str = ""


class VerdictRequest(BaseModel):
    edge_id: str
    verdict: str  # "aprobar" | "modificar" | "rechazar"


# ---------------------------------------------------------------------------
# API JSON
# ---------------------------------------------------------------------------
@app.get("/api/status")
def api_status() -> Dict[str, Any]:
    return {
        "registered_users": 1,
        "local_model_configured": True,
        "public_doi_lookup_enabled": False,
        "inference_mode": "local-only",
    }


@app.get("/api/session")
def api_session() -> Dict[str, Any]:
    return {"username": "Tet"}


@app.get("/api/projects")
def api_projects() -> Dict[str, Any]:
    return {"projects": [{"slug": e.id, "name": e.titulo} for e in ElkiaRegistry().listar()]}


@app.get("/api/usage")
def api_usage() -> Dict[str, Any]:
    return {"agents": [], "limits": {}, "usage": []}


@app.get("/api/bibliography")
def api_bibliography(project: Optional[str] = None) -> Dict[str, Any]:
    return {"project": project, "notes": [], "proposals": []}


@app.get("/api/artifacts")
def api_artifacts(project: Optional[str] = None) -> Dict[str, Any]:
    return {"project": project, "artifacts": []}


@app.get("/api/runs")
def api_runs(project: Optional[str] = None) -> Dict[str, Any]:
    return {
        "project": project,
        "plan": "",
        "draft": "",
        "review": "",
        "approved_by_agent": False,
        "revisions": 0,
        "trace": [],
    }


@app.post("/api/runs")
def api_run(req: RunRequest) -> Dict[str, Any]:
    """Ejecuta el grafo y devuelve el estado resultante."""
    try:
        config = {"configurable": {"thread_id": req.edge_id}}
        initial = {"edge_id": req.edge_id, "seed": req.seed}
        result = _graph.invoke(initial, config=config)
        return {"status": "ok", "state": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/verdict")
def api_verdict(req: VerdictRequest) -> Dict[str, Any]:
    """Reanuda el grafo con el veredicto de Tet."""
    try:
        config = {"configurable": {"thread_id": req.edge_id}}
        from langgraph.types import Command
        result = _graph.invoke(Command(resume=req.verdict), config=config)
        return {"status": "ok", "state": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models")
def api_models() -> Dict[str, Any]:
    return SuniasterUpdater().check_and_update()


# ---------------------------------------------------------------------------
# Dashboard HTML
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def dashboard_index(request: Request) -> HTMLResponse:
    return views.render_index(request)


@app.get("/edges", response_class=HTMLResponse)
def dashboard_edges(request: Request) -> HTMLResponse:
    return views.render_edges(request)


@app.get("/edges/{edge_id}", response_class=HTMLResponse)
def dashboard_edge_detail(request: Request, edge_id: str) -> HTMLResponse:
    try:
        edge = Edge.cargar(edge_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Edge no encontrado: {edge_id}")
    return views.render_edge_detail(request, edge)


@app.get("/edges/new", response_class=HTMLResponse)
def dashboard_new_edge(request: Request) -> HTMLResponse:
    return views.render_new_edge(request)


@app.post("/edges/new")
async def dashboard_create_edge(request: Request) -> JSONResponse:
    data = await request.json()
    seed = data.get("seed")
    title = data.get("title")
    from pathlib import Path
    seed_path = Path(seed) if seed else None
    edge = Edge.crear_desde_semilla(seed_path, titulo=title)
    ElkiaRegistry().registrar(edge)
    return JSONResponse({"status": "ok", "edge_id": edge.id})


@app.get("/agenda", response_class=HTMLResponse)
def dashboard_agenda(request: Request) -> HTMLResponse:
    return views.render_agenda(request)


@app.get("/artifacts/{edge_id}/{name}")
def dashboard_artifact(edge_id: str, name: str):
    path = Artifact.artifact_path(edge_id, name)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Artefacto no encontrado: {name}")
    return views.render_artifact(path)


@app.get("/dashboard/markdown")
def dashboard_markdown() -> Dict[str, Any]:
    return {"markdown": ElkiaDashboard().render_markdown()}
