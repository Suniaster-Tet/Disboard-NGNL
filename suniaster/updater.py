"""Actualizador de Suniaster: inspecciona disponibilidad de proveedores/modelos.

No modifica config.yaml automáticamente; reporta el estado para que Tet decida.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List

from suniaster.providers import ProviderUnavailable, create_model
from suniaster.router import SuniasterRouter


class SuniasterUpdater:
    """Inspecciona el estado de los modelos configurados."""

    def __init__(self, router: SuniasterRouter | None = None):
        self.router = router or SuniasterRouter()

    # ------------------------------------------------------------------ #
    # Chequeo de agentes
    # ------------------------------------------------------------------ #
    def check_and_update(self) -> Dict[str, Any]:
        details: Dict[str, Any] = {}
        errors = 0

        for agent in self.router.config.get("agents", {}):
            try:
                model = self.router.get_model_for(agent)
                details[agent] = {
                    "ok": True,
                    "model": getattr(model, "model_name", str(model)),
                }
            except (ProviderUnavailable, KeyError, ValueError) as e:
                details[agent] = {"ok": False, "error": str(e)}
                errors += 1

        status = "ok" if errors == 0 else "degraded"
        return {
            "status": status,
            "details": details,
            "agents_with_error": errors,
        }

    # ------------------------------------------------------------------ #
    # Chequeo de proveedores
    # ------------------------------------------------------------------ #
    def inspect_providers(self) -> Dict[str, Any]:
        report: Dict[str, Any] = {}
        for name, conf in self.router.config.get("providers", {}).items():
            env_key = conf.get("env_key")
            available = True if env_key is None else bool(os.getenv(env_key))
            report[name] = {
                "type": conf.get("type"),
                "free_tier": conf.get("free_tier", False),
                "requires_env": env_key,
                "available": available,
                "models": list(conf.get("models", [])),
            }
        return report

    # ------------------------------------------------------------------ #
    # Actualización (solo si Tet lo aprueba)
    # ------------------------------------------------------------------ #
    def update_config(self, suggestions: List[Dict[str, Any]], apply: bool = False) -> Dict[str, Any]:
        if not apply:
            return {"applied": False, "suggestions": suggestions}
        # Backup
        backup = Path(str(self.router.config_path) + ".bak")
        shutil.copy2(self.router.config_path, backup)
        return {"applied": False, "backup": str(backup), "suggestions": suggestions}

    # ------------------------------------------------------------------ #
    # Reporte combinado
    # ------------------------------------------------------------------ #
    def report_all(self) -> Dict[str, Any]:
        return {
            "agents": self.check_and_update(),
            "providers": self.inspect_providers(),
        }
