"""Componentes reutilizables del dashboard (helpers puros)."""
from __future__ import annotations

from typing import Any, Dict, List


def priority_badge(priority: str) -> str:
    colors = {"CRITICA": "red", "ALTA": "orange", "MEDIA": "yellow", "BAJA": "green"}
    return f'<span class="badge badge-{colors.get(priority, "grey")}">{priority}</span>'


def progress_bar(pct: float) -> str:
    pct = max(0, min(100, float(pct)))
    return (
        f'<div class="progress"><div class="progress-fill" '
        f'style="width: {pct}%"></div></div>'
    )


def edge_row(edge: Dict[str, Any]) -> str:
    return (
        f"<tr><td>{edge.get('id', '')}</td>"
        f"<td>{edge.get('titulo', '')}</td>"
        f"<td>{edge.get('estado', '')}</td>"
        f"<td>{edge.get('avance', 0)}%</td></tr>"
    )


def render_thermometer_row(t: Dict[str, Any]) -> str:
    return (
        f"<tr><td>{t.get('edge_id', '')}</td>"
        f"<td>{t.get('titulo', '')}</td>"
        f"<td>{priority_badge(t.get('prioridad', 'BAJA'))}</td>"
        f"<td>{progress_bar(t.get('avance_pct', 0))}</td>"
        f"<td>{t.get('dias_restantes', '—')}</td></tr>"
    )
