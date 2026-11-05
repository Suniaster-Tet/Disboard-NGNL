"""Sora — El Estratega (Project Manager)."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from agents.base import Agent
from core.contract import Contract
from core.edge import Edge
from core.state_schema import OverallState
from suniaster.inference import ModelUnavailable, invoke_agent


class SoraStrategist(Agent):
    nombre = "Sora"
    rol = "Estratega principal / Project Manager"

    # ------------------------------------------------------------------ #
    # Planificación
    # ------------------------------------------------------------------ #
    def plan_edge(
        self,
        edge_id: str,
        seed_prompt: str,
        bibliography: List[Dict[str, Any]] | None = None,
        theories: List[str] | None = None,
    ) -> Dict[str, Any]:
        """Descompone la idea semilla en objetivos, metas y entregables."""
        bibliography = bibliography or []
        theories = theories or []
        self.register("plan_started", {"edge_id": edge_id, "seed": seed_prompt[:80]})

        objetivos = [
            f"Responder a la idea semilla: {seed_prompt[:80]}",
            "Producir entregables verificables con trazabilidad",
        ]
        metas = [
            "Plan aprobado por Tet",
            "Evidencia bibliográfica verificada (DOI)",
            "Código y cálculos reproducibles",
        ]
        if bibliography:
            metas.append(f"Integrar {len(bibliography)} referencias aprobadas por Tet")
        entregables = [
            {"id": "E1", "descripcion": "Plan y contrato del edge",
             "agente_asignado": "Sora", "estado": "pendiente"},
            {"id": "E2", "descripcion": "Bibliografía enriquecida con DOI",
             "agente_asignado": "Jibril", "estado": "pendiente"},
            {"id": "E3", "descripcion": "Código y cálculos del proyecto",
             "agente_asignado": "Shiro", "estado": "pendiente"},
            {"id": "E4", "descripcion": "Auditoría de alineación",
             "agente_asignado": "Chlammy", "estado": "pendiente"},
        ]
        plan = {
            "edge_id": edge_id,
            "objetivos": objetivos,
            "metas": metas,
            "entregables": entregables,
            "bibliography": bibliography,
            "theories": theories,
            "avance": 0,
            "prioridad": self._priority_for(entregables),
        }
        references_context = [
            {"doi": item.get("doi"), "title": item.get("title"), "year": item.get("year")}
            for item in bibliography
        ]
        prompt = (
            "Crea un plan de investigación en JSON válido, sin markdown, con claves "
            "objetivos (lista de strings), metas (lista de strings) y entregables "
            "(lista de objetos con id, descripcion y agente_asignado). Asigna cada "
            "entregable solo a Sora, Jibril, Shiro o Chlammy. No inventes referencias: "
            "usa solo las referencias aprobadas suministradas; separa objetivos, "
            "criterios y tareas comprobables.\n"
            f"SOLICITUD: {seed_prompt}\n"
            f"TEORÍAS DEFINIDAS POR TET: {json.dumps(theories, ensure_ascii=False)}\n"
            f"REFERENCIAS APROBADAS POR TET: {json.dumps(references_context, ensure_ascii=False)}"
        )
        try:
            generated = invoke_agent("sora", prompt)
        except ModelUnavailable as error:
            plan["model_provenance"] = {"mode": "deterministic_fallback", "reason": str(error)}
            self.register("sora_model_fallback", plan["model_provenance"], level="WARNING")
            return plan
        if generated is None:
            plan["model_provenance"] = {"mode": "deterministic_fallback", "reason": "llm_disabled"}
            return plan
        try:
            allowed_dois = {
                str(item.get("doi", "")).lower() for item in bibliography if item.get("doi")
            }
            model_plan = self._parse_model_plan(generated["text"], allowed_dois)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            plan["model_provenance"] = {
                "mode": "deterministic_fallback",
                "reason": f"invalid_model_output:{type(error).__name__}",
                **{key: generated[key] for key in ("provider", "model") if key in generated},
            }
            self.register("sora_model_output_rejected", plan["model_provenance"], level="WARNING")
            return plan
        plan.update(model_plan)
        plan["model_provenance"] = {key: value for key, value in generated.items() if key != "text"}
        self.register("sora_plan_generated_by_model", plan["model_provenance"])
        return plan

    @staticmethod
    def _parse_model_plan(content: str, allowed_dois: set[str] | None = None) -> Dict[str, Any]:
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].removesuffix("```").strip()
        model_plan = json.loads(content)
        if not isinstance(model_plan, dict):
            raise TypeError("El plan debe ser un objeto JSON.")
        objectives, goals, deliverables = (
            model_plan.get("objetivos"), model_plan.get("metas"), model_plan.get("entregables")
        )
        if not isinstance(objectives, list) or not objectives or not all(isinstance(item, str) for item in objectives):
            raise ValueError("El plan debe incluir objetivos como lista de texto.")
        if not isinstance(goals, list) or not goals or not all(isinstance(item, str) for item in goals):
            raise ValueError("El plan debe incluir metas como lista de texto.")
        if not isinstance(deliverables, list) or not deliverables:
            raise ValueError("El plan debe incluir entregables.")
        allowed_agents = {"Sora", "Jibril", "Shiro", "Chlammy"}
        identifiers = set()
        for item in deliverables:
            if not isinstance(item, dict):
                raise ValueError("Cada entregable debe ser un objeto.")
            if not isinstance(item.get("id"), str) or not item["id"].strip() or item["id"] in identifiers:
                raise ValueError("Los IDs de entregable deben ser únicos y no vacíos.")
            if not isinstance(item.get("descripcion"), str) or not item["descripcion"].strip():
                raise ValueError("Cada entregable requiere una descripción.")
            if item.get("agente_asignado") not in allowed_agents:
                raise ValueError("Agente asignado no permitido.")
            identifiers.add(item["id"])
        allowed_dois = allowed_dois or set()
        text = json.dumps({"objetivos": objectives, "metas": goals, "entregables": deliverables})
        cited_dois = {
            doi.lower().rstrip(".,;)")
            for doi in re.findall(r"10\.\d{4,9}/[A-Za-z0-9._;()/:+-]+", text, re.IGNORECASE)
        }
        if not cited_dois.issubset(allowed_dois):
            raise ValueError("El plan contiene DOI no aprobados por Tet.")
        return {
            "objetivos": objectives,
            "metas": goals,
            "entregables": deliverables,
        }

    def plan_from_contract(self, edge: Edge, contract: Contract) -> Dict[str, Any]:
        """Reconstruye el plan de Sora a partir de un contrato ya aprobado."""
        return {
            "edge_id": edge.id,
            "objetivos": list(contract.objetivos),
            "metas": list(contract.metas),
            "entregables": [dict(e) for e in contract.entregables],
            "avance": edge.avance,
            "prioridad": edge.prioridad,
        }

    @staticmethod
    def _priority_for(entregables: List[Dict[str, Any]]) -> str:
        pendientes = sum(1 for e in entregables if e.get("estado") == "pendiente")
        if pendientes >= 4:
            return "alta"
        if pendientes >= 1:
            return "media"
        return "baja"

    # ------------------------------------------------------------------ #
    # Enrutamiento
    # ------------------------------------------------------------------ #
    def next_step(self, state: OverallState) -> str:
        """Decide qué agente sigue según los entregables pendientes.

        Devuelve uno de: "jibril", "shiro", "chlammy", "hitl", "fin".
        """
        entregables = state.get("entregables", [])
        pendientes = [e for e in entregables if e.get("estado", "pendiente") == "pendiente"]
        if not pendientes:
            return "fin" if state.get("status") == "COMPLETO" else "hitl"

        # Orden por dependencia: bibliografía -> ejecución -> auditoría
        prioridad = ["Jibril", "Shiro", "Chlammy"]
        for agente in prioridad:
            if any(p.get("agente_asignado") == agente for p in pendientes):
                return agente.lower()
        # Si el agente no está en la lista, se envía a Shiro por defecto
        return "shiro"

    # ------------------------------------------------------------------ #
    # Avance
    # ------------------------------------------------------------------ #
    @staticmethod
    def estimar_avance(state: OverallState) -> int:
        entregables = state.get("entregables", [])
        if not entregables:
            return 0
        entregados = sum(1 for e in entregables if e.get("estado") == "entregado")
        return int(round(entregados / len(entregables) * 100))

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #
    def execute(self, state: OverallState) -> OverallState:
        plan = self.plan_edge(
            state.get("edge_id", "edge-default"),
            state.get("seed", ""),
            bibliography=state.get("bibliography", []),
            theories=state.get("action_details", {}).get("theories", []),
        )
        state.update(plan)
        state["current_step"] = "supervisor"
        state["next_agent"] = self.next_step(state)
        self.register("plan_generated", {"entregables": len(plan["entregables"])})
        return state
