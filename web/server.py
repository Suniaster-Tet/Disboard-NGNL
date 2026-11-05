"""Servidor web local (FastAPI) con API JSON y dashboard HTML."""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from agents.jibril.agent import JibrilScientific
from core.artifact import Artifact
from core.edge import Edge
from core.log import Log
from elkia.dashboard import ElkiaDashboard
from elkia.registry import ElkiaRegistry
from suniaster.updater import SuniasterUpdater
from web.dashboard import views
from web.graph import build_graph
from web.security import DashboardSecurityMiddleware
from web.workflow import EdgeWorkflow

app = FastAPI(title="Disboard-NGNL", version="1.0.0")
app.add_middleware(DashboardSecurityMiddleware)
_graph = build_graph()


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------
class RunRequest(BaseModel):
    edge_id: str
    seed: str = ""


class EdgeCreateRequest(BaseModel):
    title: str | None = None
    seed: str = ""


class DirectRequest(BaseModel):
    text: str
    edge_id: str | None = None
    title: str | None = None


class RequestText(BaseModel):
    text: str


class PlanApprovalRequest(BaseModel):
    objetivos: list[str] | None = None
    metas: list[str] | None = None
    entregables: list[dict[str, Any]] | None = None


class BibliographySearchRequest(BaseModel):
    query: str
    limit: int = 8


class BibliographyDoiRequest(BaseModel):
    doi: str


class DecisionRequest(BaseModel):
    verdict: str
    observations: str = ""


class VerdictRequest(BaseModel):
    edge_id: str
    verdict: str  # "aprobar" | "modificar" | "rechazar"


# ---------------------------------------------------------------------------
# API JSON
# ---------------------------------------------------------------------------
@app.get("/api/status")
def api_status() -> Dict[str, Any]:
    import os

    return {
        "registered_users": 1,
        "tet_signing_configured": bool(os.getenv("TET_SIGNING_KEY")),
        "local_model_configured": bool(os.getenv("GROQ_API_KEY") or os.getenv("GOOGLE_AI_STUDIO_API_KEY")),
        "public_doi_lookup_enabled": True,
        "inference_mode": "configured-provider-or-local-tools",
    }


@app.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok"}


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
    if project:
        try:
            edges = [Edge.cargar(project)]
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=404, detail=f"Edge no encontrado: {project}"
            ) from error
    else:
        edges = ElkiaRegistry().listar()
    references = []
    for edge in edges:
        workflow = EdgeWorkflow(edge).snapshot()
        references.extend(
            {"edge_id": edge.id, **reference}
            for reference in workflow["bibliography"]
        )
    return {
        "project": project,
        "notes": [],
        "proposals": [ref for ref in references if ref["status"] == "pending_approval"],
        "references": references,
    }


@app.get("/api/artifacts")
def api_artifacts(project: Optional[str] = None) -> Dict[str, Any]:
    if project:
        try:
            edges = [Edge.cargar(project)]
        except FileNotFoundError:
            edges = []
    else:
        edges = ElkiaRegistry().listar()
    artifacts = [
        {"edge_id": edge.id, **item}
        for edge in edges
        for item in Artifact.list(edge)
    ]
    return {"project": project, "artifacts": artifacts}


@app.get("/api/runs")
def api_runs(project: Optional[str] = None) -> Dict[str, Any]:
    if not project:
        return {"project": None, "runs": []}
    return {"project": project, **_workflow(project).snapshot()}


@app.post("/api/runs")
def api_run(req: RunRequest) -> Dict[str, Any]:
    """Genera una propuesta de Sora para la solicitud enviada."""
    try:
        workflow = _workflow(req.edge_id)
        if req.seed.strip():
            workflow.add_request(req.seed)
        return {"status": "ok", "state": workflow.generate_plan()}
    except (ValueError, KeyError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/api/graph/runs")
def api_graph_run(req: RunRequest) -> Dict[str, Any]:
    """Inicia el grafo LangGraph auxiliar, reanudable mediante /api/verdict."""
    if not req.edge_id or Path(req.edge_id).name != req.edge_id or req.edge_id in {".", ".."}:
        raise HTTPException(status_code=422, detail="edge_id inválido.")
    config = {"configurable": {"thread_id": req.edge_id}}
    try:
        result = _graph.invoke(
            {"edge_id": req.edge_id, "seed": req.seed},
            config=config,
        )
        return {"status": "ok", "state": result}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


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


def _workflow(edge_id: str) -> EdgeWorkflow:
    try:
        return EdgeWorkflow(Edge.cargar(edge_id))
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"Edge no encontrado: {edge_id}") from error


def _workflow_result(operation):
    try:
        return {"status": "ok", "workflow": operation()}
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/api/edges/{edge_id}/workflow")
def api_workflow(edge_id: str) -> Dict[str, Any]:
    return _workflow(edge_id).snapshot()


@app.post("/api/requests")
def api_direct_request(request_data: DirectRequest) -> Dict[str, Any]:
    text = request_data.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Escribe una solicitud para Tet.")
    if request_data.edge_id:
        workflow = _workflow(request_data.edge_id)
    else:
        edge = Edge.crear_desde_semilla(None, titulo=request_data.title or text[:60])
        edge.ruta_seed.write_text(text + "\n", encoding="utf-8")
        ElkiaRegistry().registrar(edge)
        Log(edge.id, ruta=edge.ruta_log).registrar(
            "edge_created", {"source": "direct_request"}, agente="Tet"
        )
        workflow = EdgeWorkflow(edge)
    workflow.add_request(text)
    return {"status": "ok", "edge_id": workflow.edge.id, "workflow": workflow.generate_plan()}


@app.post("/api/edges/{edge_id}/requests")
def api_add_request(edge_id: str, request_data: RequestText) -> Dict[str, Any]:
    workflow = _workflow(edge_id)
    return _workflow_result(lambda: (workflow.add_request(request_data.text), workflow.generate_plan())[1])


@app.post("/api/edges/{edge_id}/plan")
def api_generate_plan(edge_id: str) -> Dict[str, Any]:
    workflow = _workflow(edge_id)
    return _workflow_result(workflow.generate_plan)


@app.post("/api/edges/{edge_id}/plan/approve")
def api_approve_plan(edge_id: str, edits: PlanApprovalRequest) -> Dict[str, Any]:
    workflow = _workflow(edge_id)
    return _workflow_result(lambda: workflow.approve_plan(edits.model_dump(exclude_none=True)))


@app.post("/api/edges/{edge_id}/bibliography/search")
def api_search_bibliography(edge_id: str, query: BibliographySearchRequest) -> Dict[str, Any]:
    workflow = _workflow(edge_id)
    if not query.query.strip():
        raise HTTPException(status_code=422, detail="Escribe un tema para buscar bibliografía.")
    try:
        suggestions = JibrilScientific(edge_id=edge_id).search_references(query.query, query.limit)
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Jibril no pudo consultar Crossref: {error}") from error
    for suggestion in suggestions:
        workflow.add_reference(suggestion["doi"], suggestion, proposer="Jibril")
    return {"status": "ok", "suggestions": suggestions, "workflow": workflow.snapshot()}


@app.post("/api/edges/{edge_id}/bibliography/verify")
def api_verify_bibliography(edge_id: str, request_data: BibliographyDoiRequest) -> Dict[str, Any]:
    workflow = _workflow(edge_id)
    result = JibrilScientific(edge_id=edge_id).verify_reference(request_data.doi)
    if not result["ok"]:
        raise HTTPException(status_code=422, detail=result["reason"])
    metadata = {**result["metadata"], "source": result["source"]}
    candidate = workflow.add_reference(request_data.doi, metadata, proposer="Tet")
    return {"status": "ok", "reference": candidate}


@app.post("/api/edges/{edge_id}/bibliography/{doi:path}/decision")
def api_decide_bibliography(edge_id: str, doi: str, decision: DecisionRequest) -> Dict[str, Any]:
    workflow = _workflow(edge_id)
    verdict = {
        "approve": "approve",
        "aprobar": "approve",
        "reject": "reject",
        "rechazar": "reject",
    }.get(decision.verdict)
    if not verdict:
        raise HTTPException(status_code=422, detail="Veredicto bibliográfico inválido.")
    return _workflow_result(lambda: workflow.review_reference(doi, verdict))


@app.post("/api/edges/{edge_id}/deliverables/{deliverable_id}/execute")
def api_execute_deliverable(edge_id: str, deliverable_id: str) -> Dict[str, Any]:
    workflow = _workflow(edge_id)
    return _workflow_result(lambda: workflow.execute_deliverable(deliverable_id))


@app.post("/api/edges/{edge_id}/deliverables/{deliverable_id}/decision")
def api_decide_deliverable(
    edge_id: str, deliverable_id: str, decision: DecisionRequest
) -> Dict[str, Any]:
    workflow = _workflow(edge_id)
    verdict = {
        "approve": "approve", "aprobar": "approve",
        "modify": "modify", "modificar": "modify",
        "reject": "reject", "rechazar": "reject",
    }.get(decision.verdict)
    if not verdict:
        raise HTTPException(status_code=422, detail="Veredicto inválido.")
    return _workflow_result(
        lambda: workflow.review_deliverable(deliverable_id, verdict, decision.observations)
    )


@app.post("/api/edges/{edge_id}/deliverables/{deliverable_id}/artifacts")
async def api_upload_artifact(
    edge_id: str, deliverable_id: str, file: UploadFile = File(...)
) -> Dict[str, Any]:
    workflow = _workflow(edge_id)
    filename = Path(file.filename or "artifact.bin").name
    content = await file.read(25 * 1024 * 1024 + 1)
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="El tamaño máximo del archivo es 25 MiB.")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / filename
            source.write_bytes(content)
            state = workflow.submit_artifact(deliverable_id, source, filename)
        return {"status": "ok", "workflow": state}
    except (ValueError, KeyError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    finally:
        await file.close()


@app.post("/api/edges/{edge_id}/final/decision")
def api_decide_final(edge_id: str, decision: DecisionRequest) -> Dict[str, Any]:
    workflow = _workflow(edge_id)
    verdict = {
        "approve": "approve", "aprobar": "approve",
        "modify": "modify", "modificar": "modify",
        "reject": "reject", "rechazar": "reject",
    }.get(decision.verdict)
    if not verdict:
        raise HTTPException(status_code=422, detail="Veredicto final inválido.")
    return _workflow_result(lambda: workflow.decide_final(verdict, decision.observations))


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


@app.get("/edges/new", response_class=HTMLResponse)
def dashboard_new_edge(request: Request) -> HTMLResponse:
    return views.render_new_edge(request)


@app.get("/edges/{edge_id}", response_class=HTMLResponse)
def dashboard_edge_detail(request: Request, edge_id: str) -> HTMLResponse:
    try:
        edge = Edge.cargar(edge_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Edge no encontrado: {edge_id}")
    return views.render_edge_detail(request, edge)


@app.post("/edges/new")
def dashboard_create_edge(data: EdgeCreateRequest) -> JSONResponse:
    edge = Edge.crear_desde_semilla(None, titulo=data.title)
    if data.seed.strip():
        edge.ruta_seed.write_text(data.seed.strip() + "\n", encoding="utf-8")
    ElkiaRegistry().registrar(edge)
    Log(edge.id, ruta=edge.ruta_log).registrar(
        "edge_created", {"has_seed": bool(data.seed.strip())}, agente="Tet"
    )
    workflow = EdgeWorkflow(edge)
    if data.seed.strip():
        workflow.add_request(data.seed)
        workflow.generate_plan()
    return JSONResponse({"status": "ok", "edge_id": edge.id})


@app.get("/agenda", response_class=HTMLResponse)
def dashboard_agenda(request: Request) -> HTMLResponse:
    return views.render_agenda(request)


@app.get("/artifacts/{edge_id}/{name}")
def dashboard_artifact(edge_id: str, name: str):
    try:
        edge = Edge.cargar(edge_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Edge no encontrado: {edge_id}")
    entry = next((item for item in Artifact.list(edge) if item.get("name") == name), None)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Artefacto no encontrado: {name}")
    try:
        path = Artifact.artifact_path(edge_id, name)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Artefacto no encontrado: {name}")
    artifact = Artifact(edge_id=edge_id, name=name, path=path, agent="", sha256=entry.get("sha256", ""))
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"Artefacto no encontrado: {name}")
    if not artifact.verify():
        raise HTTPException(status_code=409, detail=f"El hash del artefacto no coincide: {name}")
    return views.render_artifact(path)


@app.get("/dashboard/markdown")
def dashboard_markdown() -> Dict[str, Any]:
    return {"markdown": ElkiaDashboard().render_markdown()}
