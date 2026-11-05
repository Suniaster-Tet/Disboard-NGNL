"""Registro de edges activos en Elkia.

Mantiene el índice de proyectos (edges) y su estado. Es la fuente de verdad
para `disboard status` y para el enrutamiento de Sora.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.edge import Edge

REGISTRY_PATH = Path("edges/elkia_registry.json")
LEGACY_REGISTRY_PATH = Path("edges/elkia_registro.json")

ALLOWED_UPDATE_FIELDS = {"titulo", "avance", "prioridad", "estado"}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class ElkiaRegistry:
    """Registro persistente de edges en Elkia."""

    def __init__(self, ruta: Path = REGISTRY_PATH):
        self.ruta = Path(ruta)
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        # Migración transparente desde el nombre antiguo
        legacy = self.ruta.parent / LEGACY_REGISTRY_PATH.name
        if not self.ruta.exists() and legacy.exists():
            self.ruta.write_text(legacy.read_text(encoding="utf-8"), encoding="utf-8")
        if not self.ruta.exists():
            self._guardar({"edges": {}})

    # ------------------------------------------------------------------ #
    # Persistencia interna
    # ------------------------------------------------------------------ #
    def _cargar(self) -> Dict[str, Any]:
        return json.loads(self.ruta.read_text(encoding="utf-8"))

    def _guardar(self, datos: Dict[str, Any]) -> None:
        self.ruta.write_text(
            json.dumps(datos, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------ #
    # API pública
    # ------------------------------------------------------------------ #
    def registrar(self, edge: Edge) -> None:
        """Registra un edge recién creado."""
        datos = self._cargar()
        datos["edges"][edge.id] = {
            "titulo": edge.titulo,
            "ruta": str(edge.ruta),
            "avance": edge.avance,
            "prioridad": edge.prioridad,
            "estado": edge.estado,
            "creado_en": edge.creado_en,
            "actualizado_en": _utcnow(),
        }
        self._guardar(datos)

    def actualizar(self, edge_id: str, **campos: Any) -> None:
        """Actualiza campos de un edge registrado."""
        invalidos = set(campos) - ALLOWED_UPDATE_FIELDS
        if invalidos:
            raise ValueError(f"Campos no permitidos: {sorted(invalidos)}")
        datos = self._cargar()
        if edge_id not in datos["edges"]:
            raise KeyError(f"Edge no registrado en Elkia: {edge_id}")
        datos["edges"][edge_id].update(campos)
        datos["edges"][edge_id]["actualizado_en"] = _utcnow()
        self._guardar(datos)

    def eliminar(self, edge_id: str) -> bool:
        datos = self._cargar()
        if edge_id not in datos["edges"]:
            return False
        del datos["edges"][edge_id]
        self._guardar(datos)
        return True

    def listar(self) -> List[Edge]:
        """Devuelve todos los edges registrados como objetos Edge."""
        datos = self._cargar()
        edges: List[Edge] = []
        for edge_id in datos["edges"]:
            try:
                edges.append(Edge.cargar(edge_id))
            except FileNotFoundError:
                continue
        return edges

    def listar_meta(self) -> Dict[str, Dict[str, Any]]:
        """Devuelve los metadatos del registro sin cargar cada Edge."""
        return dict(self._cargar().get("edges", {}))

    def obtener(self, edge_id: str) -> Optional[Edge]:
        try:
            return Edge.cargar(edge_id)
        except FileNotFoundError:
            return None

    def existe(self, edge_id: str) -> bool:
        return edge_id in self._cargar()["edges"]

    def resumen(self) -> Dict[str, Dict[str, int]]:
        datos = self._cargar().get("edges", {})
        por_estado: Dict[str, int] = {}
        por_prioridad: Dict[str, int] = {}
        for meta in datos.values():
            est = meta.get("estado", "NUEVO")
            pri = meta.get("prioridad", "media")
            por_estado[est] = por_estado.get(est, 0) + 1
            por_prioridad[pri] = por_prioridad.get(pri, 0) + 1
        return {"por_estado": por_estado, "por_prioridad": por_prioridad}
