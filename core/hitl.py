"""HITL: aprobación de Tet con firma HMAC-SHA256 e integración con LangGraph."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from core.log import Log


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clave() -> str:
    clave = os.getenv("TET_SIGNING_KEY")
    if not clave:
        raise RuntimeError(
            "Falta TET_SIGNING_KEY. Configúrala en .env (ver .env.example)."
        )
    return clave


def _serializar(payload: Dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")


def generar_firma_tet(payload: Dict[str, Any], clave: str | None = None) -> str:
    """Genera la firma HMAC-SHA256 de una aprobación de Tet."""
    secreto = (clave or _clave()).encode("utf-8")
    return hmac.new(secreto, _serializar(payload), hashlib.sha256).hexdigest()


def verificar_firma_tet(payload: Dict[str, Any], firma: str, clave: str | None = None) -> bool:
    """Verifica la firma HMAC-SHA256 de una aprobación de Tet."""
    esperada = generar_firma_tet(payload, clave)
    return hmac.compare_digest(esperada, firma)


def firmar_aprobacion(payload: Dict[str, Any], clave: str | None = None) -> Dict[str, Any]:
    """Devuelve el payload y su firma, listos para guardar en el log."""
    return {"payload": payload, "firma": generar_firma_tet(payload, clave), "ts": _utcnow()}


def solicitar_aprobacion_tet(state: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Evalúa el veredicto de Tet y actualiza el estado.

    Devuelve (decision, state) con decision ∈ {"proceed", "rollback", "modify"}.
    """
    edge_id = state.get("edge_id", "edge-desconocido")
    veredicto = str(state.get("tet_feedback", "")).strip().lower()
    accion = state.get("action_details", {})
    log = Log(edge_id)
    contexto = {"step": state.get("current_step")}

    if veredicto in {"1", "aprobar", "aprobado", "approve", "approved"}:
        payload = {"edge_id": edge_id, "action": accion, "ts": _utcnow()}
        firma = generar_firma_tet(payload)
        firmas = list(state.get("signatures", []))
        firmas.append({"agent": "Tet", "signature": firma, "timestamp": payload["ts"]})
        state["signatures"] = firmas
        state["status"] = "COMPLETO" if state.get("current_step") == "final" else "EN_PROCESO"
        log.registrar("tet_approved", {"firma": firma}, agente="Tet", contexto=contexto)
        return "proceed", state

    if veredicto in {"3", "rechazar", "rechazado", "reject", "rejected"}:
        rollback = list(state.get("rollback_log", []))
        rollback.append({"accion": accion, "ts": _utcnow()})
        state["rollback_log"] = rollback
        state["status"] = "EN_REVISION"
        log.registrar("tet_rejected", {"accion": accion}, agente="Tet", contexto=contexto)
        return "rollback", state

    state["status"] = "EN_REVISION"
    log.registrar(
        "tet_observations",
        {"veredicto": veredicto},
        agente="Tet",
        nivel="WARNING",
        contexto=contexto,
    )
    return "modify", state
