"""Registro de plugins de Disboard-NGNL.

Permite registrar plugins con contrato versionado y allowlist explícita.
Diseñado para que `disboard_ext` pueda aportar implementaciones sin romper
el núcleo.
"""
from __future__ import annotations

import importlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

CONTRACT_VERSION = 1


@dataclass(frozen=True)
class PluginDescriptor:
    id: str
    kind: str
    version: str
    contract_version: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PluginRegistry:
    """Registro de plugins con allowlist y contrato versionado."""

    def __init__(self) -> None:
        self._plugins: Dict[tuple[str, str], Any] = {}
        self._descriptors: List[PluginDescriptor] = []

    # ------------------------------------------------------------------ #
    # Registro
    # ------------------------------------------------------------------ #
    def register(
        self,
        descriptor: PluginDescriptor,
        plugin: Any,
        replace_existing: bool = False,
    ) -> None:
        if descriptor.contract_version != CONTRACT_VERSION:
            raise ValueError(
                f"Contrato incompatible: {descriptor.contract_version} != {CONTRACT_VERSION}"
            )
        clave = (descriptor.kind, descriptor.id)
        if clave in self._plugins and not replace_existing:
            raise ValueError(f"El plugin '{descriptor.id}' ya está registrado.")
        self._plugins[clave] = plugin
        self._descriptors = [
            d for d in self._descriptors
            if not (d.kind == descriptor.kind and d.id == descriptor.id)
        ]
        self._descriptors.append(descriptor)

    def get(self, kind: str, plugin_id: str) -> Any:
        clave = (kind, plugin_id)
        if clave not in self._plugins:
            raise KeyError(f"Plugin no encontrado: {kind}/{plugin_id}")
        return self._plugins[clave]

    def list(self) -> List[PluginDescriptor]:
        return list(self._descriptors)

    def listar_por_kind(self, kind: str) -> List[PluginDescriptor]:
        return [d for d in self._descriptors if d.kind == kind]

    def desregistrar(self, kind: str, plugin_id: str) -> bool:
        clave = (kind, plugin_id)
        if clave not in self._plugins:
            return False
        del self._plugins[clave]
        self._descriptors = [
            d for d in self._descriptors
            if not (d.kind == kind and d.id == plugin_id)
        ]
        return True

    # ------------------------------------------------------------------ #
    # Allowlist
    # ------------------------------------------------------------------ #
    def load_allowlist(self, manifest_path: Path) -> None:
        """Carga plugins desde un manifiesto JSON con allowlist de módulos."""
        datos = json.loads(manifest_path.read_text(encoding="utf-8"))
        if datos.get("contract_version") != CONTRACT_VERSION:
            raise ValueError("Contrato incompatible en el manifiesto.")
        for entrada in datos.get("plugins", []):
            if not entrada.get("enabled", True):
                continue
            modulo = entrada.get("module", "")
            if not modulo.startswith("disboard_ext"):
                raise ValueError(
                    "Solo se permiten módulos del paquete 'disboard_ext'."
                )
            mod = importlib.import_module(modulo)
            factory = getattr(mod, entrada.get("factory", "create_plugin"), None)
            if factory is None:
                raise ValueError(f"El módulo {modulo} no expone una factory válida.")
            plugin = factory()
            descriptor = PluginDescriptor(
                id=entrada["id"],
                kind=entrada["kind"],
                version=entrada["version"],
                contract_version=entrada["contract_version"],
            )
            self.register(
                descriptor, plugin, replace_existing=entrada.get("replace", False)
            )


def create_default_registry() -> PluginRegistry:
    """Crea un registro con los plugins por defecto."""
    from disboard_ext.local_artifact_store import create_plugin as create_storage

    registry = PluginRegistry()
    registry.register(
        PluginDescriptor("local-filesystem", "storage", "1.0.0", CONTRACT_VERSION),
        create_storage(),
    )
    return registry
