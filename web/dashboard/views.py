"""Vistas HTML del dashboard."""
from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any, Dict

from fastapi import Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from core.artifact import Artifact
from core.contract import Contract
from core.edge import Edge
from core.log import Log
from elkia.dashboard import ElkiaDashboard
from elkia.registry import ElkiaRegistry

TEMPLATES = Jinja2Templates(directory="web/templates")


def _base_context(request: Request, **extra: Any) -> Dict[str, Any]:
    return {
        "request": request,
        "app_name": "Disboard-NGNL",
        **extra,
    }


def render_index(request: Request) -> HTMLResponse:
    registry = ElkiaRegistry()
    dashboard = ElkiaDashboard(registro=registry)
    return TEMPLATES.TemplateResponse(
        request=request,
        name="index.html",
        context=_base_context(
            request,
            edges=registry.listar(),
            thermometers=dashboard.listar_termometros(),
            summary=registry.resumen(),
        ),
    )


def render_edges(request: Request) -> HTMLResponse:
    registry = ElkiaRegistry()
    return TEMPLATES.TemplateResponse(
        request=request,
        name="index.html",
        context=_base_context(request, edges=registry.listar(), thermometers=[]),
    )


def render_edge_detail(request: Request, edge: Edge) -> HTMLResponse:
    contract = None
    if edge.ruta_contrato.exists():
        contract = Contract.cargar(edge.ruta_contrato)
    log = Log(edge.id).leer() if edge.ruta_log.exists() else []
    artifacts = [
        a for a in Artifact.list(edge)
        if a.get("name")
    ]
    return TEMPLATES.TemplateResponse(
        request=request,
        name="edge_detail.html",
        context=_base_context(
            request,
            edge=edge,
            contract=contract,
            log_entries=log,
            artifacts=artifacts,
        ),
    )


def render_new_edge(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse(
        request=request,
        name="edge_detail.html",
        context=_base_context(
            request, edge=None, contract=None, log_entries=[], artifacts=[], is_new=True
        ),
    )


def render_agenda(request: Request) -> HTMLResponse:
    registry = ElkiaRegistry()
    return TEMPLATES.TemplateResponse(
        request=request,
        name="index.html",
        context=_base_context(request, edges=registry.listar(), thermometers=[], agenda=True),
    )


def render_artifact(path: Path):
    suffix = path.suffix.lower()
    if suffix in {".html", ".md", ".txt"}:
        return HTMLResponse(f"<pre>{escape(path.read_text(encoding='utf-8'))}</pre>")
    return FileResponse(path, filename=path.name)
