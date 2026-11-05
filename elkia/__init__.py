"""Elkia: entorno de trabajo y registro de edges de Disboard-NGNL."""

__version__ = "2.0.0"

from elkia.registry import ElkiaRegistry
from elkia.rules import BoardRules
from elkia.state import EdgeState
from elkia.dashboard import EdgePriority, EdgeThermometer, ElkiaDashboard

__all__ = [
    "ElkiaRegistry",
    "BoardRules",
    "EdgeState",
    "ElkiaDashboard",
    "EdgePriority",
    "EdgeThermometer",
]
