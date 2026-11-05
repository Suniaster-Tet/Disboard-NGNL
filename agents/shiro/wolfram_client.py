"""Cliente de Wolfram Alpha (uso único de Shiro).

Si falta WOLFRAM_API_KEY, `evaluate_expression` devuelve estado "mock" para
que Suniaster asigne un proveedor alternativo. `resolve` sigue lanzando
`WolframUnavailable` para uso directo.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional


class WolframUnavailable(RuntimeError):
    """Se lanza cuando falta WOLFRAM_API_KEY y el llamador exige Wolfram."""


class WolframClient:
    def __init__(self, app_id: Optional[str] = None):
        self.app_id = app_id or os.getenv("WOLFRAM_API_KEY", "")

    @property
    def available(self) -> bool:
        return bool(self.app_id)

    # ------------------------------------------------------------------ #
    # Uso tolerante (no lanza; devuelve mock)
    # ------------------------------------------------------------------ #
    def evaluate_expression(self, expr: str) -> Dict[str, Any]:
        if not self.available:
            return {
                "status": "mock",
                "expr": expr,
                "warning": "Sin WOLFRAM_API_KEY; Suniaster asignará proveedor alternativo.",
            }
        try:
            import wolframalpha
            client = wolframalpha.Client(self.app_id)
            res = client.query(expr)
            return {
                "status": "success",
                "expr": expr,
                "result": "\n".join(p.text for p in res.results),
            }
        except Exception as e:
            return {"status": "error", "expr": expr, "error": str(e)}

    # ------------------------------------------------------------------ #
    # Uso estricto (lanza si no hay key)
    # ------------------------------------------------------------------ #
    def resolve(self, consulta: str) -> str:
        if not self.available:
            raise WolframUnavailable("Falta WOLFRAM_API_KEY.")
        result = self.evaluate_expression(consulta)
        if result["status"] != "success":
            raise WolframUnavailable(result.get("error", "Wolfram no disponible"))
        return result["result"]
