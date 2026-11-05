"""Shiro — Analista Lógico (código y cálculos)."""
from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

from agents.base import Agent
from core.state_schema import OverallState

try:
    from agents.shiro.wolfram_client import WolframClient, WolframUnavailable
    HAS_WOLFRAM = True
except ImportError:  # pragma: no cover
    WolframClient = None
    WolframUnavailable = Exception
    HAS_WOLFRAM = False


class ShiroAnalyst(Agent):
    nombre = "Shiro"
    rol = "Analista lógico / Código y precisión"

    # ------------------------------------------------------------------ #
    # Generación de código
    # ------------------------------------------------------------------ #
    def generate_tdd_code(self, specification: str) -> Tuple[str, str]:
        code = (
            "# Implementación generada por Shiro\n"
            "def solve_algorithm(x: float) -> float:\n"
            "    return x ** 2 + 1.0\n"
        )
        test_code = (
            "# Test unitario generado por Shiro\n"
            "import unittest\n"
            "from app import solve_algorithm\n\n"
            "class TestShiroLogic(unittest.TestCase):\n"
            "    def test_solution(self):\n"
            "        self.assertEqual(solve_algorithm(2.0), 5.0)\n"
        )
        return code, test_code

    # ------------------------------------------------------------------ #
    # Wolfram
    # ------------------------------------------------------------------ #
    def wolfram_available(self) -> bool:
        return bool(os.getenv("WOLFRAM_API_KEY")) and HAS_WOLFRAM

    def generate_wolfram_script(self, equation: str) -> str:
        return (
            "(* Wolfram Language Script generado por Shiro *)\n"
            f"Solve[{equation}, x]\n"
        )

    def validate_wolfram_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if result.get("status") == "mock":
            return {
                "valid": False,
                "reason": "Sin WOLFRAM_API_KEY; Suniaster asignó proveedor alternativo.",
                "requires_tet_validation": True,
            }
        return {"valid": True, "reason": ""}

    def record_provider_used(self, provider: str, reason: str = "") -> None:
        self.register(
            "shiro_provider_used",
            {"provider": provider, "reason": reason},
            level="WARNING" if provider != "wolfram" else "INFO",
        )

    # ------------------------------------------------------------------ #
    # Tensores
    # ------------------------------------------------------------------ #
    def analyze_tensor(self, izuna, tensor_name: str, dimensions: List[str]) -> Dict[str, Any]:
        """Solicita a Izuna un tensor proyectado para su análisis."""
        if not izuna.verificar_tensor(tensor_name):
            return {
                "status": "error",
                "message": f"Tensor corrupto o inexistente: {tensor_name}",
            }
        projected = izuna.proyectar(tensor_name, dimensions)
        return {
            "status": "ok",
            "tensor": projected["esquema"]["nombre"],
            "registros": projected["esquema"]["registros"],
            "dimensiones": projected["esquema"]["dimensiones"],
        }

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #
    def execute(self, state: OverallState) -> OverallState:
        deliverables = state.get("entregables", [])
        results: List[Dict[str, Any]] = []
        for d in deliverables:
            if d.get("agente_asignado") != "Shiro":
                continue
            code, test_code = self.generate_tdd_code(d.get("descripcion", ""))
            provider = "wolfram" if self.wolfram_available() else "google"
            if provider != "wolfram":
                self.record_provider_used(provider, reason="missing_wolfram_key")
            results.append({
                "entregable": d["id"],
                "code": code,
                "test": test_code,
                "provider_used": provider,
                "wolfram_available": self.wolfram_available(),
            })

        state["artifacts"] = state.get("artifacts", []) + [r["entregable"] for r in results]
        state["action_details"]["shiro_results"] = results
        state["current_step"] = "chlammy_review"
        self.register("deliverables_generated", {"n": len(results)})
        return state
