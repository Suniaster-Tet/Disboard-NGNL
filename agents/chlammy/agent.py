"""Chlammy Zell — Auditora (antes Kurami)."""
from __future__ import annotations

from typing import Any, Dict, List

from agents.base import Agent
from core.state_schema import OverallState


class ChlammyAuditor(Agent):
    nombre = "Chlammy Zell"
    rol = "Auditora / Subagente de Sora"

    # ------------------------------------------------------------------ #
    # Alineación con contrato
    # ------------------------------------------------------------------ #
    def verify_contract_alignment(
        self,
        contract: Dict[str, Any],
        deliverables: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        problems: List[str] = []
        if not deliverables:
            problems.append("No hay entregables para evaluar.")
        if not contract.get("objetivos"):
            problems.append("El contrato no tiene objetivos.")
        return {
            "aligned": not problems,
            "compliance_score": 100.0 if not problems else 0.0,
            "notes": problems,
        }

    # ------------------------------------------------------------------ #
    # Alineación bibliográfica
    # ------------------------------------------------------------------ #
    def verify_reference_alignment(
        self,
        deliverables: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        missing_doi = [
            d.get("id", "?") for d in deliverables
            if d.get("tipo") == "bibliografia" and not d.get("doi_verificado")
        ]
        return {
            "aligned": not missing_doi,
            "missing_doi": missing_doi,
        }

    # ------------------------------------------------------------------ #
    # Revisión de código y matemáticas
    # ------------------------------------------------------------------ #
    def review_code_and_math(self, code: str, math_claims: str) -> Dict[str, Any]:
        issues: List[str] = []
        if "division" in math_claims.lower() and "zero" not in code.lower():
            issues.append("Posible división por cero no controlada.")
        if "log(" in code and "x <= 0" not in code:
            issues.append("Posible logaritmo de valor no positivo sin control.")
        return {
            "status": "APPROVED" if not issues else "NEEDS_REVISION",
            "issues_found": issues,
        }

    # ------------------------------------------------------------------ #
    # Rollback
    # ------------------------------------------------------------------ #
    def verify_rollback(self, rollback_log: List[Dict[str, Any]]) -> Dict[str, Any]:
        problems = [
            r for r in rollback_log
            if not r.get("accion") or not r.get("ts")
        ]
        return {"valid": not problems, "problems": problems}

    # ------------------------------------------------------------------ #
    # Resumen
    # ------------------------------------------------------------------ #
    def summarize(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "APPROVED" if result.get("aligned") else "NEEDS_REVISION",
            "score": result.get("compliance_score", 0.0),
            "notes": result.get("notes", []),
        }

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #
    def execute(self, state: OverallState) -> OverallState:
        contract = state.get("action_details", {}).get("contract", {})
        deliverables = state.get("artifacts", [])
        result = self.verify_contract_alignment(contract, deliverables)
        state["action_details"]["audit"] = result
        state["current_step"] = "hitl"
        self.register(
            "audit_completed",
            result,
            level="INFO" if result["aligned"] else "WARNING",
        )
        return state
