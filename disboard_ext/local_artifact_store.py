"""Built-in local artifact storage plugin for Disboard-NGNL.

Este plugin es el `storage/local-filesystem` registrado por defecto en
`core/plugins.py`. Expone las acciones `list`, `save` y `verify` a través de
`LocalArtifactStorePlugin.run(root, action, ...)`.

El `root` que recibe es la raíz del edge (por ejemplo, `edges/edge-foo`).
Los artefactos viven en `root/artifacts/`. Si se pasa `edge_id`, se usa
`root/edge_id/artifacts/` (útil cuando `root` es `edges/`).
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class LocalArtifactStore:
    """Almacén local de artefactos con verificación SHA-256."""

    def __init__(self, root_dir: Union[str, Path], edge_id: Optional[str] = None):
        self.root_dir = Path(root_dir)
        if edge_id:
            self.artifacts_dir = self.root_dir / edge_id / "artifacts"
        else:
            self.artifacts_dir = self.root_dir / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Operaciones
    # ------------------------------------------------------------------ #
    def save_artifact(self, name: str, content: Union[bytes, str]) -> Dict[str, Any]:
        """Guarda un artefacto y devuelve su hash SHA-256."""
        target = self.artifacts_dir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode("utf-8") if isinstance(content, str) else content
        target.write_bytes(data)
        return {
            "status": "success",
            "name": name,
            "path": str(target),
            "sha256": hashlib.sha256(data).hexdigest(),
            "size_bytes": len(data),
        }

    def verify_artifact(self, name: str, expected_sha256: str) -> bool:
        """Verifica la integridad de un artefacto contra un SHA-256 esperado."""
        target = self.artifacts_dir / name
        if not target.exists():
            return False
        return hashlib.sha256(target.read_bytes()).hexdigest() == expected_sha256

    def list_artifacts(self) -> List[Dict[str, Any]]:
        """Devuelve la lista de artefactos registrados en el directorio."""
        result: List[Dict[str, Any]] = []
        for path in sorted(self.artifacts_dir.rglob("*")):
            if not path.is_file():
                continue
            data = path.read_bytes()
            result.append({
                "name": str(path.relative_to(self.artifacts_dir)),
                "sha256": hashlib.sha256(data).hexdigest(),
                "size_bytes": len(data),
            })
        return result


class LocalArtifactStorePlugin:
    """Plugin v1 para `disboard_ext`."""

    def run(self, root, action, *args, **kwargs):
        edge_id = kwargs.pop("edge_id", None)
        store = LocalArtifactStore(root, edge_id=edge_id)

        if action in {"list", "list_artifacts"}:
            return store.list_artifacts()
        if action in {"save", "save_artifact"}:
            return store.save_artifact(*args, **kwargs)
        if action in {"verify", "verify_artifact"}:
            return store.verify_artifact(*args, **kwargs)

        raise ValueError(f"Acción de almacenamiento no permitida: {action}")


def create_plugin() -> LocalArtifactStorePlugin:
    return LocalArtifactStorePlugin()
