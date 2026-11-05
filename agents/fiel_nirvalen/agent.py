"""Fiel Nirvalen — Asistencia Administrativa (subagente de Dola)."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from agents.base import Agent
from agents.fiel_nirvalen.privacy_filter import filter_sensitive_data
from core.log import Log
from core.state_schema import OverallState


class FielNirvalen(Agent):
    nombre = "Fiel Nirvalen"
    rol = "Asistencia administrativa / Subagente de Dola"

    def __init__(self, edge_id: Optional[str] = None, root_dir: str = "."):
        super().__init__(edge_id)
        self.root_dir = Path(root_dir)

    # ------------------------------------------------------------------ #
    # Agenda
    # ------------------------------------------------------------------ #
    def _agenda_path(self) -> Optional[Path]:
        if not self.edge_id:
            return None
        return Path("edges") / self.edge_id / "agenda.md"

    def load_agenda(self) -> List[str]:
        path = self._agenda_path()
        if not path or not path.exists():
            return []
        return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def save_agenda(self, items: List[str]) -> Path:
        path = self._agenda_path()
        if path is None:
            raise ValueError("Se requiere edge_id para guardar la agenda.")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(items) + "\n", encoding="utf-8")
        self.register("agenda_saved", {"items": len(items)})
        return path

    # ------------------------------------------------------------------ #
    # Privacidad
    # ------------------------------------------------------------------ #
    @staticmethod
    def anonymize_text(text: str) -> str:
        return filter_sensitive_data(text)

    # ------------------------------------------------------------------ #
    # Informes
    # ------------------------------------------------------------------ #
    def summary_by_agent(self) -> Dict[str, int]:
        if not self.edge_id:
            return {}
        resumen = Log(self.edge_id).resumen()
        return resumen.get("por_agente", {})

    def compile_executive_report(
        self,
        edge_or_state: Union[str, OverallState],
        history: List[str],
    ) -> str:
        edge_id = (
            edge_or_state.get("edge_id", "edge-desconocido")
            if isinstance(edge_or_state, dict)
            else edge_or_state
        )
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            f"# Reporte ejecutivo — {edge_id}",
            f"**Fecha:** {ts}",
            "",
            "## Hitos aprobados",
        ]
        lines += [f"{i}. {h}" for i, h in enumerate(history, 1)]
        resumen = self.summary_by_agent()
        if resumen:
            lines += ["", "## Actividad por agente"]
            lines += [f"- {ag}: {n}" for ag, n in sorted(resumen.items())]
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Correo
    # ------------------------------------------------------------------ #
    def draft_anonymized_email(
        self, recipient_role: str, subject: str, raw_body: str
    ) -> str:
        body = filter_sensitive_data(raw_body)
        return (
            f"ASUNTO: {subject}\n"
            f"PARA: {recipient_role}\n\n"
            f"{body}\n\n-- Disboard-NGNL"
        )

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #
    def execute(self, state: OverallState) -> OverallState:
        self.register("assistance_executed", {"edge_id": state.get("edge_id")})
        return state
