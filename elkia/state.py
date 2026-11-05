"""Estado de un edge: avance y prioridad (termómetros de Sora)."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Literal

Prioridad = Literal["alta", "media", "baja"]

PRIORIDAD_COLOR = {
    "alta": "rojo",
    "media": "amarillo",
    "baja": "verde",
}


@dataclass
class EdgeState:
    avance: int = 0
    prioridad: Prioridad = "media"
    estado: str = "NUEVO"

    def __post_init__(self) -> None:
        self.avance = max(0, min(100, int(self.avance)))
        if self.prioridad not in PRIORIDAD_COLOR:
            self.prioridad = "media"

    def avanzar(self, pct: int) -> None:
        self.avance = max(0, min(100, self.avance + int(pct)))

    def porcentaje(self) -> str:
        return f"{self.avance}%"

    def porcentaje_legible(self) -> str:
        icono = "🟢" if self.avance == 100 else "🟡" if self.avance >= 50 else "🔴"
        return f"{icono} {self.avance}%"

    def prioridad_legible(self) -> str:
        return {"alta": "🔴 Alta", "media": "🟡 Media", "baja": "🟢 Baja"}[self.prioridad]

    def color(self) -> str:
        return PRIORIDAD_COLOR[self.prioridad]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, datos: Dict[str, Any]) -> "EdgeState":
        return cls(
            avance=int(datos.get("avance", 0)),
            prioridad=datos.get("prioridad", "media"),
            estado=datos.get("estado", "NUEVO"),
        )
