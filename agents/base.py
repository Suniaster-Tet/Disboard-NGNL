"""Interfaz común de agentes de Disboard-NGNL."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

from core.log import Log
from core.state_schema import OverallState

SKILLS_ROOT = Path("skills")

# Mapa agente → carpeta de skill (nombres en inglés, ver estructura §6)
SKILL_MAP: Dict[str, str] = {
    "Sora": "sora-planning",
    "Shiro": "shiro-execution",
    "Stephanie Dola": "stephanie-review",
    "Fiel Nirvalen": "fiel-assistance",
    "Izuna": "izuna-data-engineering",
    "Jibril": "jibril-bibliography",
    "Chlammy Zell": "chlammy-alignment",
}


class Agent(ABC):
    nombre: str = "agente"
    rol: str = ""

    def __init__(self, edge_id: str | None = None):
        self.edge_id = edge_id
        self._log: Log | None = Log(edge_id) if edge_id else None

    # ------------------------------------------------------------------ #
    # Skill
    # ------------------------------------------------------------------ #
    @classmethod
    def load_skill(cls, agent: str | None = None) -> str:
        """Carga el contenido del SKILL.md del agente."""
        name = agent or cls.nombre
        folder = SKILL_MAP.get(name)
        if not folder:
            raise KeyError(f"Agente sin skill registrada: {name}")
        path = SKILLS_ROOT / folder / "SKILL.md"
        if not path.exists():
            raise FileNotFoundError(f"No se encontró el skill: {path}")
        return path.read_text(encoding="utf-8")

    @classmethod
    def available_skills(cls) -> List[str]:
        return sorted(SKILL_MAP)

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #
    @abstractmethod
    def execute(self, state: OverallState) -> OverallState:
        ...

    # ------------------------------------------------------------------ #
    # Auditoría
    # ------------------------------------------------------------------ #
    def register(
        self,
        event: str,
        details: Dict[str, Any] | None = None,
        level: str = "INFO",
    ) -> None:
        if self._log:
            self._log.registrar(event, details, agente=self.nombre, nivel=level)
