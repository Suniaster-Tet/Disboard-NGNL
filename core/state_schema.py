"""Esquema global del estado del grafo LangGraph de Disboard-NGNL.

Alineado con el README:
- §1: avance y prioridad del edge.
- §2.2: patrón supervisor con Sora, Jibril, Shiro, Chlammy.
- §4: HITL con interrupt/resume.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict

EstadoEdge = Literal["NUEVO", "EN_PROCESO", "EN_REVISION", "COMPLETO"]
Prioridad = Literal["alta", "media", "baja"]
Decision = Literal["proceed", "rollback", "modify"]
Agente = Literal[
    "sora", "jibril", "shiro", "chlammy", "hitl", "fin", "suniaster_updater"
]


class Entregable(TypedDict, total=False):
    id: str
    descripcion: str
    agente_asignado: str
    estado: Literal["pendiente", "en_proceso", "entregado", "rechazado"]


class OverallState(TypedDict, total=False):
    # --- Identidad del edge ---
    edge_id: str
    seed: str
    titulo: str

    # --- Plan de Sora (README §1) ---
    objetivos: List[str]
    metas: List[str]
    entregables: List[Entregable]
    avance: int
    prioridad: Prioridad

    # --- Enrutamiento ---
    next_agent: Optional[Agente]
    assigned_agent: Optional[str]
    pending_deliverables: List[str]

    # --- Resultados de agentes ---
    bibliography: List[Dict[str, Any]]
    artifacts: List[str]
    artifact_metadata: Dict[str, Dict[str, Any]]
    signatures: List[Dict[str, Any]]

    # --- HITL ---
    tet_feedback: str
    tet_verdict: Optional[Decision]
    interrupt_payload: Optional[Dict[str, Any]]
    rollback_log: List[Dict[str, Any]]
    pending_modifications: List[Dict[str, Any]]
    action_details: Dict[str, Any]

    # --- Estado y auditoría ---
    status: EstadoEdge
    current_step: str
    trace_id: str
    timestamp: str
    started_at: Optional[str]
    finished_at: Optional[str]
    checkpointer_backend: Optional[str]
