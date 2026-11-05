"""Dashboard de seguimiento táctico de Elkia.

Calcula la prioridad de cada edge a partir de los días restantes (matriz de
Eisenhower simplificada) y renderiza un tablero de control agregado.

Reutiliza `EdgeState` para el avance y `ElkiaRegistry` para listar edges.
No reimplementa lógica de estado ni de persistencia.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Iterable, List, Optional

from core.edge import Edge
from elkia.registry import ElkiaRegistry
from elkia.state import EdgeState

FECHA_OBJETIVO = re.compile(r"Fecha objetivo:\s*(\d{4}-\d{2}-\d{2})")


class EdgePriority(Enum):
    CRITICA = "rojo"
    ALTA = "naranja"
    MEDIA = "amarillo"
    BAJA = "verde"


@dataclass
class EdgeThermometer:
    """Vista de un edge para el dashboard."""
    edge_id: str
    titulo: str
    prioridad: EdgePriority
    avance_pct: float
    dias_restantes: Optional[int]
    estado: str


class ElkiaDashboard:
    """Tablero de control y seguimiento de edges."""

    def __init__(self, registro: Optional[ElkiaRegistry] = None):
        self.registro = registro or ElkiaRegistry()

    # ------------------------------------------------------------------ #
    # Cálculo de prioridad
    # ------------------------------------------------------------------ #
    @staticmethod
    def compute_priority(dias_restantes: Optional[int]) -> EdgePriority:
        if dias_restantes is None:
            return EdgePriority.BAJA
        if dias_restantes <= 3:
            return EdgePriority.CRITICA
        if dias_restantes <= 7:
            return EdgePriority.ALTA
        if dias_restantes <= 14:
            return EdgePriority.MEDIA
        return EdgePriority.BAJA

    @staticmethod
    def _dias_restantes(edge: Edge) -> Optional[int]:
        contract = edge.ruta_contrato
        if not contract.exists():
            return None
        m = FECHA_OBJETIVO.search(contract.read_text(encoding="utf-8"))
        if not m:
            return None
        try:
            fecha = date.fromisoformat(m.group(1))
        except ValueError:
            return None
        return (fecha - date.today()).days

    # ------------------------------------------------------------------ #
    # Construcción de termómetros
    # ------------------------------------------------------------------ #
    def _termometro(
        self, edge: Edge, dias_restantes: Optional[int]
    ) -> EdgeThermometer:
        state = EdgeState(avance=edge.avance, prioridad=edge.prioridad, estado=edge.estado)
        return EdgeThermometer(
            edge_id=edge.id,
            titulo=edge.titulo,
            prioridad=self.compute_priority(dias_restantes),
            avance_pct=float(state.avance),
            dias_restantes=dias_restantes,
            estado=state.estado,
        )

    def listar_termometros(
        self,
        dias_por_edge: Optional[dict[str, int]] = None,
    ) -> List[EdgeThermometer]:
        dias_por_edge = dias_por_edge or {}
        termometros: List[EdgeThermometer] = []
        for edge in self.registro.listar():
            dias = dias_por_edge.get(edge.id, self._dias_restantes(edge))
            termometros.append(self._termometro(edge, dias))
        return termometros

    def filtrar(
        self,
        estado: Optional[str] = None,
        prioridad: Optional[str] = None,
    ) -> List[EdgeThermometer]:
        termometros = self.listar_termometros()
        if estado:
            termometros = [t for t in termometros if t.estado == estado]
        if prioridad:
            termometros = [t for t in termometros if t.prioridad.name.lower() == prioridad]
        return termometros

    # ------------------------------------------------------------------ #
    # Render
    # ------------------------------------------------------------------ #
    def render_markdown(
        self,
        termometros: Optional[Iterable[EdgeThermometer]] = None,
    ) -> str:
        if termometros is None:
            termometros = self.listar_termometros()

        lineas = [
            "# 🏰 Tablero de Control y Seguimiento Elkia",
            "",
            "| ID Edge | Título | Prioridad | Avance (%) | Días restantes | Estado |",
            "| :--- | :--- | :---: | :---: | :---: | :---: |",
        ]
        termometros = list(termometros)
        if not termometros:
            lineas.append("| — | _Sin edges activos_ | — | — | — | — |")
        else:
            for t in termometros:
                dias = f"{t.dias_restantes}d" if t.dias_restantes is not None else "—"
                lineas.append(
                    f"| `{t.edge_id}` | {t.titulo} | `{t.prioridad.value.upper()}` "
                    f"| {t.avance_pct}% | {dias} | {t.estado} |"
                )
        return "\n".join(lineas)

    # Alias retrocompatible
    def render_dashboard(
        self,
        termometros: Optional[Iterable[EdgeThermometer]] = None,
    ) -> str:
        return self.render_markdown(termometros)

    def render_json(self) -> str:
        return json.dumps(
            [asdict(t) for t in self.listar_termometros()],
            ensure_ascii=False,
            default=str,
        )
