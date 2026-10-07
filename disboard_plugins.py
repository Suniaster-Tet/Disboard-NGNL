"""Explicit, versioned plugin contracts for replaceable Disboard blocks."""
from __future__ import annotations

import importlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


CONTRACT_VERSION = 1
PLUGIN_ID = re.compile(r"^[a-z][a-z0-9_.-]{1,79}$")
PLUGIN_VERSION = re.compile(r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$")
PLUGIN_KINDS = {
    "storage",
    "ingest",
    "transform",
    "agent_provider",
    "report",
    "interface",
}
TRUSTED_MODULE_PREFIXES = ("disboard_ext_", "disboard_ext.")


class Plugin(Protocol):
    def run(self, *args: Any, **kwargs: Any) -> Any: ...


@dataclass(frozen=True)
class PluginDescriptor:
    plugin_id: str
    kind: str
    version: str
    contract_version: int


@dataclass(frozen=True)
class RegisteredPlugin:
    descriptor: PluginDescriptor
    implementation: Plugin


class PluginRegistry:
    """Load only explicitly configured, trusted extensions; never scan the workspace."""

    def __init__(self, contract_version: int = CONTRACT_VERSION):
        self.contract_version = contract_version
        self._plugins: dict[tuple[str, str], RegisteredPlugin] = {}

    def register(
        self,
        descriptor: PluginDescriptor,
        implementation: Plugin,
        *,
        replace_existing: bool = False,
    ) -> None:
        if not PLUGIN_ID.fullmatch(descriptor.plugin_id):
            raise ValueError(f"Identificador de plugin inválido: {descriptor.plugin_id}")
        if descriptor.kind not in PLUGIN_KINDS:
            raise ValueError(f"Tipo de plugin no soportado: {descriptor.kind}")
        if not PLUGIN_VERSION.fullmatch(descriptor.version):
            raise ValueError(f"Versión semántica inválida: {descriptor.version}")
        if descriptor.contract_version != self.contract_version:
            raise ValueError(
                f"Contrato incompatible: se requiere v{self.contract_version}, "
                f"plugin declara v{descriptor.contract_version}."
            )
        if not callable(getattr(implementation, "run", None)):
            raise TypeError("El plugin debe implementar run(*args, **kwargs).")

        key = (descriptor.kind, descriptor.plugin_id)
        if key in self._plugins and not replace_existing:
            raise ValueError(f"El plugin ya está registrado: {key}")
        self._plugins[key] = RegisteredPlugin(descriptor, implementation)

    def get(self, kind: str, plugin_id: str) -> Plugin:
        try:
            return self._plugins[(kind, plugin_id)].implementation
        except KeyError as error:
            raise LookupError(f"No existe plugin registrado: {kind}/{plugin_id}") from error

    def list(self) -> list[PluginDescriptor]:
        return sorted(
            (entry.descriptor for entry in self._plugins.values()),
            key=lambda item: (item.kind, item.plugin_id),
        )

    def load_allowlist(self, manifest_path: str | Path) -> None:
        manifest_file = Path(manifest_path)
        config = json.loads(manifest_file.read_text(encoding="utf-8"))
        if config.get("contract_version") != self.contract_version:
            raise ValueError("La versión del contrato del manifiesto no es compatible.")
        entries = config.get("plugins")
        if not isinstance(entries, list):
            raise ValueError("El manifiesto debe definir una lista 'plugins'.")
        for entry in entries:
            if not isinstance(entry, dict) or entry.get("enabled") is not True:
                continue
            module_name = entry.get("module", "")
            if not isinstance(module_name, str) or not module_name.startswith(
                TRUSTED_MODULE_PREFIXES
            ):
                raise ValueError(
                    "Solo se permiten módulos de extensión con prefijo "
                    "'disboard_ext_' o 'disboard_ext.'."
                )
            module = importlib.import_module(module_name)
            factory = getattr(module, entry.get("factory", "create_plugin"), None)
            if not callable(factory):
                raise TypeError(f"El módulo {module_name} no expone una factory válida.")
            implementation = factory()
            descriptor = PluginDescriptor(
                plugin_id=entry.get("id", ""),
                kind=entry.get("kind", ""),
                version=entry.get("version", ""),
                contract_version=entry.get("contract_version", -1),
            )
            self.register(
                descriptor,
                implementation,
                replace_existing=entry.get("replace", False) is True,
            )


def create_default_registry(root: str | Path | None = None) -> PluginRegistry:
    from disboard_ext.local_artifact_store import create_plugin

    registry = PluginRegistry()
    registry.register(
        PluginDescriptor(
            plugin_id="local-filesystem",
            kind="storage",
            version="1.0.0",
            contract_version=CONTRACT_VERSION,
        ),
        create_plugin(),
    )
    if root is not None:
        manifest_path = Path(root) / "disboard_plugins.json"
        if manifest_path.is_file():
            registry.load_allowlist(manifest_path)
    return registry
