"""Gestión de artefactos (entregables) producidos por los agentes."""
from __future__ import annotations

import hashlib
import mimetypes
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.edge import Edge
from core.log import Log


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for bloque in iter(lambda: f.read(8192), b""):
            h.update(bloque)
    return h.hexdigest()


@dataclass
class Artifact:
    edge_id: str
    name: str
    path: Path
    agent: str
    sha256: str = ""
    created_at: str = field(default_factory=_utcnow)
    mime_type: str = ""
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------ #
    # Registro
    # ------------------------------------------------------------------ #
    @classmethod
    def register(
        cls,
        edge: Edge,
        source: Path,
        agent: str,
        target_relative: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Artifact":
        artifact_root = (edge.ruta / "artifacts").resolve()
        target = (artifact_root / (target_relative or source.name)).resolve()
        if not target.is_relative_to(artifact_root):
            raise ValueError("La ruta del artefacto debe permanecer dentro del edge.")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        mime, _ = mimetypes.guess_type(str(target))
        artifact = cls(
            edge_id=edge.id,
            name=target.name,
            path=target,
            agent=agent,
            sha256=_sha256(target),
            mime_type=mime or "application/octet-stream",
            size_bytes=target.stat().st_size,
            metadata=metadata or {},
        )
        Log(edge.id, ruta=edge.ruta_log).registrar(
            "artifact_registered",
            {
                "name": artifact.name,
                "sha256": artifact.sha256,
                "size_bytes": artifact.size_bytes,
                "mime_type": artifact.mime_type,
            },
            agente=agent,
        )
        return artifact

    # ------------------------------------------------------------------ #
    # Verificación
    # ------------------------------------------------------------------ #
    def verify(self) -> bool:
        if not self.path.exists():
            return False
        return _sha256(self.path) == self.sha256

    # ------------------------------------------------------------------ #
    # Rollback (README §2.1)
    # ------------------------------------------------------------------ #
    def delete(self, reason: str = "rechazo de Tet") -> None:
        if self.path.exists():
            self.path.unlink()
        Log(self.edge_id).registrar(
            "artifact_deleted",
            {"name": self.name, "reason": reason},
            agente=self.agent,
        )

    # ------------------------------------------------------------------ #
    # Listado
    # ------------------------------------------------------------------ #
    @staticmethod
    def list(edge: Edge) -> List[Dict[str, Any]]:
        log = Log(edge.id, ruta=edge.ruta_log)
        events = log.leer_por_evento("artifact_registered")
        return [e.get("detalles", {}) for e in events]

    @staticmethod
    def artifact_path(edge_id: str, name: str) -> Path:
        edge = Edge.cargar(edge_id)
        artifact_root = (edge.ruta / "artifacts").resolve()
        path = (artifact_root / name).resolve()
        if not path.is_relative_to(artifact_root):
            raise ValueError("La ruta del artefacto debe permanecer dentro del edge.")
        return path

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
