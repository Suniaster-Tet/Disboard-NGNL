"""Plantillas de seguimiento reutilizables de Sora.

- Diagrama de flujo de entregables (Mermaid).
- Matriz de Eisenhower (Markdown).
- Línea de tiempo (Mermaid gantt).
- Tabla resumen (Markdown).
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List


def _escape(texto: str) -> str:
    return str(texto).replace('"', "'").replace("|", "/")


def render_tracking_mermaid(entregables: Iterable[Dict[str, Any]]) -> str:
    """Diagrama de flujo de entregables (Mermaid)."""
    entregables = list(entregables)
    lineas = ["flowchart TD"]
    for e in entregables:
        eid = e.get("id", "?")
        desc = _escape(e.get("descripcion", ""))[:40]
        agente = _escape(e.get("agente_asignado", "?"))
        estado = _escape(e.get("estado", "pendiente"))
        lineas.append(f'    {eid}["{desc}<br/>({agente})<br/>[{estado}]"]')
    ids = [e.get("id") for e in entregables]
    for a, b in zip(ids, ids[1:]):
        lineas.append(f"    {a} --> {b}")
    return "\n".join(lineas)


def render_timeline(entregables: Iterable[Dict[str, Any]]) -> str:
    """Línea de tiempo (Mermaid gantt) de los entregables."""
    entregables = list(entregables)
    lineas = [
        "gantt",
        "    title Secuencia de entregables",
        "    dateFormat  YYYY-MM-DD",
        "    axisFormat  %d/%m",
    ]
    for i, e in enumerate(entregables, 1):
        eid = _escape(e.get("id", f"E{i}"))
        agente = _escape(e.get("agente_asignado", "?"))
        lineas.append(f"    {eid} [{agente}] :e{i}, 1d")
    return "\n".join(lineas)


def to_markdown_table(entregables: Iterable[Dict[str, Any]]) -> str:
    """Tabla Markdown resumen de entregables."""
    lineas = [
        "| ID | Descripción | Agente | Estado |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for e in entregables:
        lineas.append(
            f"| `{e.get('id', '?')}` | {e.get('descripcion', '')} "
            f"| {e.get('agente_asignado', '?')} "
            f"| {e.get('estado', 'pendiente')} |"
        )
    return "\n".join(lineas)


def render_eisenhower_matrix(termometros: List[Dict[str, Any]]) -> str:
    """Matriz de Eisenhower a partir de los termómetros del dashboard.

    Cada termómetro debe tener `edge_id`, `titulo`, `prioridad`, `avance_pct`.
    """
    cuadrantes = {
        "urgente_importante": [],
        "importante": [],
        "urgente": [],
        "ninguno": [],
    }
    for t in termometros:
        pri = str(t.get("prioridad", "BAJA")).upper()
        avance = float(t.get("avance_pct", 0))
        if pri in ("ROJO", "CRITICA"):
            cuadrantes["urgente_importante"].append(t)
        elif pri == "ALTA":
            cuadrantes["importante"].append(t)
        elif pri == "MEDIA":
            cuadrantes["urgente"].append(t)
        else:
            cuadrantes["ninguno"].append(t)

    lineas = ["# Matriz de Eisenhower", ""]
    titulos = {
        "urgente_importante": "Q1 · URGENTE E IMPORTANTE",
        "importante": "Q2 · IMPORTANTE, NO URGENTE",
        "urgente": "Q3 · URGENTE, NO IMPORTANTE",
        "ninguno": "Q4 · NO URGENTE NI IMPORTANTE",
    }
    for key, titulo in titulos.items():
        lineas.append(f"## {titulo}")
        lineas.append("")
        if not cuadrantes[key]:
            lineas.append("_Sin edges_")
        else:
            lineas.append("| Edge | Título | Avance |")
            lineas.append("| :--- | :--- | :---: |")
            for t in cuadrantes[key]:
                lineas.append(
                    f"| `{t.get('edge_id', '?')}` | {t.get('titulo', '')} "
                    f"| {t.get('avance_pct', 0)}% |"
                )
        lineas.append("")
    return "\n".join(lineas)
