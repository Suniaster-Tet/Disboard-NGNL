"""Núcleo compartido de Disboard-NGNL.

Expone los tipos y utilidades que consola y web comparten:
- Edge y Contract (proyectos)
- Log (auditoría)
- Artifact (entregables)
- HITL (aprobación de Tet)
- StateSchema (grafo LangGraph)
- Checkpointer (durable o SQLite)
- Plugins (extensibilidad controlada)
"""

from core.edge import Edge
from core.contract import Contract
from core.log import Log
from core.artifact import Artifact
from core.hitl import (
    firmar_aprobacion,
    generar_firma_tet,
    solicitar_aprobacion_tet,
    verificar_firma_tet,
)
from core.state_schema import OverallState
from core.checkpointer import DisboardCheckpointer
from core.plugins import (
    CONTRACT_VERSION,
    PluginDescriptor,
    PluginRegistry,
    create_default_registry,
)

__all__ = [
    # Núcleo
    "Edge",
    "Contract",
    "Log",
    "Artifact",
    # HITL
    "firmar_aprobacion",
    "generar_firma_tet",
    "verificar_firma_tet",
    "solicitar_aprobacion_tet",
    # Estado
    "OverallState",
    # Checkpointer
    "DisboardCheckpointer",
    # Plugins
    "CONTRACT_VERSION",
    "PluginDescriptor",
    "PluginRegistry",
    "create_default_registry",
]
