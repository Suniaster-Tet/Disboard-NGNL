"""Shiro — Analista Lógico (código y cálculos)."""
from __future__ import annotations

import ast
import json
import os
import re
from typing import Any, Dict, List, Tuple

from agents.base import Agent
from core.state_schema import OverallState
from suniaster.inference import ModelUnavailable, invoke_agent

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
    def generate_tdd_code(
        self,
        specification: str,
        bibliography: List[Dict[str, Any]] | None = None,
        theories: List[str] | None = None,
    ) -> Tuple[str, str]:
        """Genera TDD con modelo configurado o devuelve un scaffold no ejecutable."""
        bibliography = bibliography or []
        theories = theories or []
        references = [
            {"doi": item.get("doi"), "title": item.get("title"), "year": item.get("year")}
            for item in bibliography
        ]
        prompt = (
            "Diseña una implementación Python y pruebas unittest en JSON válido con "
            "claves code y test, ambas strings. No ejecutes código ni inventes resultados. "
            "Documenta supuestos, límites y qué afirmaciones se apoyan en cada DOI. "
            "Respeta estrictamente la especificación, teorías y referencias proporcionadas.\n"
            f"ESPECIFICACIÓN: {specification}\n"
            f"TEORÍAS APROBADAS POR TET: {json.dumps(theories, ensure_ascii=False)}\n"
            f"REFERENCIAS APROBADAS POR TET: {json.dumps(references, ensure_ascii=False)}"
        )
        try:
            generated = invoke_agent("shiro", prompt)
        except ModelUnavailable as error:
            self._generation_metadata = {
                "mode": "scaffold_fallback", "reason": str(error), "provider": None, "model": None
            }
            self.register("shiro_model_fallback", self._generation_metadata, level="WARNING")
            return self._fallback_tdd_code(specification)
        if generated is None:
            self._generation_metadata = {
                "mode": "scaffold_fallback", "reason": "llm_disabled", "provider": None, "model": None
            }
            return self._fallback_tdd_code(specification)
        try:
            result = json.loads(generated["text"])
            code, test_code = result["code"], result["test"]
            if not isinstance(code, str) or not isinstance(test_code, str):
                raise ValueError("El modelo debe devolver code y test como texto.")
            if len(code) > 200_000 or len(test_code) > 200_000:
                raise ValueError("El código generado supera el límite de tamaño.")
            ast.parse(code)
            ast.parse(test_code)
            allowed_dois = {
                str(item.get("doi", "")).lower() for item in bibliography if item.get("doi")
            }
            cited_dois = {
                doi.lower().rstrip(".,;)")
                for doi in re.findall(
                    r"10\.\d{4,9}/[A-Za-z0-9._;()/:+-]+", code + "\n" + test_code, re.IGNORECASE
                )
            }
            if not cited_dois.issubset(allowed_dois):
                raise ValueError("El código cita DOI no autorizados por Tet.")
        except (json.JSONDecodeError, KeyError, TypeError, ValueError, SyntaxError) as error:
            self._generation_metadata = {
                "mode": "scaffold_fallback",
                "reason": f"invalid_model_output:{type(error).__name__}",
                **{key: generated[key] for key in ("provider", "model") if key in generated},
            }
            self.register("shiro_model_output_rejected", self._generation_metadata, level="WARNING")
            return self._fallback_tdd_code(specification)
        self._generation_metadata = {
            "mode": "model",
            **{key: generated[key] for key in ("provider", "model") if key in generated},
            "references": [item.get("doi") for item in bibliography if item.get("doi")],
            "theories": theories,
        }
        self.register("shiro_model_output_accepted", self._generation_metadata)
        return code, test_code

    @staticmethod
    def _fallback_tdd_code(specification: str) -> Tuple[str, str]:
        safe_specification = json.dumps(specification, ensure_ascii=True)
        code = (
            "def solve_algorithm(*args, **kwargs):\n"
            f"    \\\"\\\"\\\"TODO: implement the approved specification {safe_specification}.\\\"\\\"\\\"\n"
            "    raise NotImplementedError(\"No free-tier model response is available; implement and review this scaffold.\")\n"
        )
        test_code = (
            "import unittest\n\n"
            "from implementation import solve_algorithm\n\n\n"
            "class TestApprovedSpecification(unittest.TestCase):\n"
            "    def test_implementation_is_pending(self):\n"
            "        with self.assertRaises(NotImplementedError):\n"
            "            solve_algorithm()\n"
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
            code, test_code = self.generate_tdd_code(
                d.get("descripcion", ""),
                bibliography=state.get("bibliography", []),
                theories=state.get("action_details", {}).get("theories", []),
            )
            provider = "wolfram" if self.wolfram_available() else "google"
            if provider != "wolfram":
                self.record_provider_used(provider, reason="missing_wolfram_key")
            results.append({
                "entregable": d["id"],
                "code": code,
                "test": test_code,
                "provider_used": provider,
                "wolfram_available": self.wolfram_available(),
                "model_provenance": getattr(self, "_generation_metadata", {}),
            })

        state["artifacts"] = state.get("artifacts", []) + [r["entregable"] for r in results]
        state["action_details"]["shiro_results"] = results
        state["current_step"] = "chlammy_review"
        self.register("deliverables_generated", {"n": len(results)})
        return state
