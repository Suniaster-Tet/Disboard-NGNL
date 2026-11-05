"""Contrato del edge: objetivos, metas y entregables aprobados por Tet."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.edge import Edge


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Contract:
    edge_id: str
    objetivos: List[str] = field(default_factory=list)
    metas: List[str] = field(default_factory=list)
    entregables: List[Dict[str, Any]] = field(default_factory=list)
    theories: List[str] = field(default_factory=list)
    bibliography: List[Dict[str, Any]] = field(default_factory=list)
    aprobado_por_tet: bool = False
    aprobado_en: str = ""
    creado_en: str = field(default_factory=_utcnow)
    actualizado_en: str = field(default_factory=_utcnow)
    firma_tet: str = ""  # no se serializa a Markdown por seguridad

    # ------------------------------------------------------------------ #
    # Construcción
    # ------------------------------------------------------------------ #
    @classmethod
    def desde_plan_sora(cls, edge: Edge, plan: Dict[str, Any]) -> "Contract":
        """Crea un contrato a partir del plan propuesto por Sora."""
        return cls(
            edge_id=edge.id,
            objetivos=list(plan.get("objetivos", [])),
            metas=list(plan.get("metas", [])),
            entregables=list(plan.get("entregables", [])),
            theories=list(plan.get("theories", [])),
            bibliography=list(plan.get("bibliography", [])),
        )

    # ------------------------------------------------------------------ #
    # Aprobación HITL
    # ------------------------------------------------------------------ #
    def aprobar(self, firma_tet: str) -> None:
        """Registra la aprobación de Tet con su firma HMAC."""
        if not firma_tet:
            raise ValueError("Se requiere la firma de Tet para aprobar el contrato.")
        self.aprobado_por_tet = True
        self.aprobado_en = _utcnow()
        self.actualizado_en = self.aprobado_en
        self.firma_tet = firma_tet

    # ------------------------------------------------------------------ #
    # Validación
    # ------------------------------------------------------------------ #
    def validar(self) -> List[str]:
        errores: List[str] = []
        if not self.edge_id:
            errores.append("El contrato debe tener edge_id.")
        if not self.objetivos:
            errores.append("El contrato no tiene objetivos.")
        if not self.metas:
            errores.append("El contrato no tiene metas.")
        if not self.entregables:
            errores.append("El contrato no tiene entregables.")
        return errores

    # ------------------------------------------------------------------ #
    # Persistencia (Markdown legible por humanos y por agentes)
    # ------------------------------------------------------------------ #
    def to_markdown(self) -> str:
        lineas = [
            f"# Contrato del edge `{self.edge_id}`",
            "",
            f"- Aprobado por Tet: **{'sí' if self.aprobado_por_tet else 'no'}**",
            f"- Aprobado en: `{self.aprobado_en or 'pendiente'}`",
            f"- Creado en: `{self.creado_en}`",
            f"- Actualizado en: `{self.actualizado_en}`",
            "",
            "## Objetivos",
            *[f"- {o}" for o in self.objetivos],
            "",
            "## Metas",
            *[f"- {m}" for m in self.metas],
            "",
            "## Teorías y marcos definidos por Tet",
            *[f"- {theory}" for theory in self.theories],
            "",
            "## Bibliografía aprobada por Tet",
            *[
                f"- `{item.get('doi', '')}` — {item.get('title', '')}"
                + (f" ({item.get('year')})" if item.get("year") else "")
                + (f" · fuente: {item.get('source')}" if item.get("source") else "")
                for item in self.bibliography
            ],
            "",
            "## Entregables",
            *[f"- `{e.get('id', '?')}` — {e.get('descripcion', '')}"
              for e in self.entregables],
            "",
        ]
        return "\n".join(lineas)

    def guardar(self, ruta: Path) -> None:
        ruta.write_text(self.to_markdown(), encoding="utf-8")

    @classmethod
    def cargar(cls, ruta: Path) -> "Contract":
        """Carga un contrato desde su representación Markdown (parser mínimo)."""
        texto = ruta.read_text(encoding="utf-8")
        edge_id = ""
        objetivos: List[str] = []
        metas: List[str] = []
        entregables: List[Dict[str, Any]] = []
        theories: List[str] = []
        bibliography: List[Dict[str, Any]] = []
        aprobado_por_tet = False
        aprobado_en = ""
        seccion = None
        for linea in texto.splitlines():
            if linea.startswith("# Contrato del edge"):
                edge_id = linea.split("`")[1]
            elif linea.startswith("- Aprobado por Tet:"):
                aprobado_por_tet = "sí" in linea.lower()
            elif linea.startswith("- Aprobado en:"):
                aprobado_en = linea.split("`")[1] if "`" in linea else ""
            elif linea.startswith("## "):
                seccion = linea[3:].strip().lower()
            elif linea.startswith("- ") and seccion == "objetivos":
                objetivos.append(linea[2:])
            elif linea.startswith("- ") and seccion == "metas":
                metas.append(linea[2:])
            elif linea.startswith("- ") and seccion == "teorías y marcos definidos por tet":
                theories.append(linea[2:])
            elif linea.startswith("- `") and seccion == "bibliografía aprobada por tet":
                doi, _, citation = linea[3:].partition("` — ")
                title, _, rest = citation.partition(" · fuente: ")
                bibliography.append({"doi": doi, "title": title, "source": rest})
            elif linea.startswith("- `") and seccion == "entregables":
                partes = linea[2:].split("` — ", 1)
                entregables.append({
                    "id": partes[0].strip("`"),
                    "descripcion": partes[1] if len(partes) > 1 else "",
                })
        return cls(
            edge_id=edge_id,
            objetivos=objetivos,
            metas=metas,
            entregables=entregables,
            theories=theories,
            bibliography=bibliography,
            aprobado_por_tet=aprobado_por_tet,
            aprobado_en=aprobado_en,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
