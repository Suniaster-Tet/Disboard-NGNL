"""Log estructurado por edge (auditoría, README §3)."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class Log:
    """Registro append-only en JSONL por edge."""

    def __init__(
        self,
        edge_id: str,
        ruta: Optional[Path] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.edge_id = edge_id
        if ruta is None:
            ruta = Path("edges") / edge_id / "log.jsonl"
        self.ruta = ruta
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logger or logging.getLogger("disboard.edges")

    def registrar(
        self,
        evento: str,
        detalles: Optional[Dict[str, Any]] = None,
        agente: Optional[str] = None,
        nivel: str = "INFO",
        contexto: Optional[Dict[str, Any]] = None,
    ) -> None:
        entrada = {
            "timestamp": _utcnow(),
            "edge_id": self.edge_id,
            "agente": agente,
            "evento": evento,
            "nivel": nivel,
            "detalles": detalles or {},
            "contexto": contexto or {},
        }
        with self.ruta.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
        # Espejo en logging estándar (config/logging.yaml)
        nivel_log = getattr(logging, nivel.upper(), logging.INFO)
        self.logger.log(nivel_log, f"{agente or '-'} | {evento}", extra={"edge_id": self.edge_id})

    # ------------------------------------------------------------------ #
    # Lectura
    # ------------------------------------------------------------------ #
    def leer(self) -> List[Dict[str, Any]]:
        if not self.ruta.exists():
            return []
        with self.ruta.open("r", encoding="utf-8") as f:
            return [json.loads(linea) for linea in f if linea.strip()]

    def leer_por_agente(self, agente: str) -> List[Dict[str, Any]]:
        return [e for e in self.leer() if e.get("agente") == agente]

    def leer_por_evento(self, evento: str) -> List[Dict[str, Any]]:
        return [e for e in self.leer() if e.get("evento") == evento]

    def resumen(self) -> Dict[str, Dict[str, int]]:
        por_agente: Dict[str, int] = {}
        por_evento: Dict[str, int] = {}
        for e in self.leer():
            ag = e.get("agente") or "desconocido"
            ev = e.get("evento") or "desconocido"
            por_agente[ag] = por_agente.get(ag, 0) + 1
            por_evento[ev] = por_evento.get(ev, 0) + 1
        return {"por_agente": por_agente, "por_evento": por_evento}
