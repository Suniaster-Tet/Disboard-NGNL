"""Modelo de un edge (proyecto) en Disboard-NGNL.

Un edge representa una partida de investigación: nace de una idea semilla de
Tet, tiene un contrato, un log y artefactos. Su estado (avance y prioridad)
se registra en Elkia.
"""
from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

EDGES_ROOT = Path("edges")

PRIORIDADES = {"alta", "media", "baja"}
ESTADOS = {"NUEVO", "EN_PROCESO", "EN_REVISION", "COMPLETO"}


def _slugify(texto: str) -> str:
    texto = re.sub(r"[^\w\s-]", "", texto.lower()).strip()
    return re.sub(r"[-\s]+", "-", texto)[:40] or "edge"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Edge:
    id: str
    titulo: str
    ruta: Path
    creado_en: str = field(default_factory=_utcnow)
    avance: int = 0
    prioridad: str = "media"
    estado: str = "NUEVO"

    def __post_init__(self) -> None:
        self.avance = max(0, min(100, int(self.avance)))
        if self.prioridad not in PRIORIDADES:
            self.prioridad = "media"
        if self.estado not in ESTADOS:
            self.estado = "NUEVO"
        if not isinstance(self.ruta, Path):
            self.ruta = Path(self.ruta)

    # ------------------------------------------------------------------ #
    # Constructores
    # ------------------------------------------------------------------ #
    @classmethod
    def crear_desde_semilla(
        cls,
        semilla: Optional[Path],
        titulo: Optional[str] = None,
        ruta_edges: Optional[Path] = None,
    ) -> "Edge":
        """Crea un edge a partir de una idea semilla de Tet."""
        base = titulo or (semilla.stem if semilla else "nuevo-edge")
        edge_id = f"edge-{_slugify(base)}-{uuid.uuid4().hex[:6]}"
        root = Path(ruta_edges) if ruta_edges else EDGES_ROOT
        ruta = root / edge_id
        (ruta / "artifacts").mkdir(parents=True, exist_ok=True)
        (ruta / "out").mkdir(parents=True, exist_ok=True)

        edge = cls(id=edge_id, titulo=base, ruta=ruta)
        edge.guardar_metadatos()
        if semilla and semilla.exists():
            (ruta / "seed.md").write_text(
                semilla.read_text(encoding="utf-8"), encoding="utf-8"
            )
        return edge

    # ------------------------------------------------------------------ #
    # Persistencia
    # ------------------------------------------------------------------ #
    @property
    def ruta_metadatos(self) -> Path:
        return self.ruta / "edge.json"

    @property
    def ruta_contrato(self) -> Path:
        return self.ruta / "contract.md"

    @property
    def ruta_log(self) -> Path:
        return self.ruta / "log.jsonl"

    @property
    def ruta_seed(self) -> Path:
        return self.ruta / "seed.md"

    # Alias retrocompatible (deprecado)
    @property
    def ruta_bitacora(self) -> Path:
        return self.ruta_log

    def guardar_metadatos(self) -> None:
        self.ruta.mkdir(parents=True, exist_ok=True)
        self.ruta_metadatos.write_text(
            json.dumps(asdict(self), indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    @classmethod
    def cargar(cls, edge_id: str, ruta_edges: Optional[Path] = None) -> "Edge":
        root = Path(ruta_edges) if ruta_edges else EDGES_ROOT
        ruta = root / edge_id / "edge.json"
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        datos["ruta"] = Path(datos["ruta"])
        return cls(**datos)

    @classmethod
    def from_dict(cls, datos: Dict[str, Any]) -> "Edge":
        datos = dict(datos)
        datos["ruta"] = Path(datos["ruta"])
        return cls(**datos)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    # ------------------------------------------------------------------ #
    # Estado
    # ------------------------------------------------------------------ #
    def actualizar_estado(
        self,
        avance: Optional[int] = None,
        prioridad: Optional[str] = None,
        estado: Optional[str] = None,
    ) -> None:
        if avance is not None:
            self.avance = max(0, min(100, int(avance)))
        if prioridad is not None and prioridad in PRIORIDADES:
            self.prioridad = prioridad
        if estado is not None and estado in ESTADOS:
            self.estado = estado
        self.guardar_metadatos()
