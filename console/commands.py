"""Comandos de la consola HITL (start, continue, approve, reject)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from agents.sora.agent import SoraStrategist
from console.presentation import Presentation
from core.contract import Contract
from core.edge import Edge
from core.hitl import solicitar_aprobacion_tet
from core.log import Log
from elkia.registry import ElkiaRegistry


def start(seed: Optional[Path], title: Optional[str] = None) -> int:
 """Inicia un edge, genera plan de Sora y espera aprobación de Tet."""
 if seed and not seed.exists():
     print(f"✖ No se encontró la semilla: {seed}")
     return 2

 edge = Edge.crear_desde_semilla(seed, titulo=title)
 Log(edge.id).registrar(
     "edge_created",
     {"seed": str(seed) if seed else None},
     agente="Tet",
 )
 ElkiaRegistry().registrar(edge)

 print(f"\n✔ Edge creado: {edge.id}")
 print(f"➜ Ruta: {edge.ruta}")

 sora = SoraStrategist(edge_id=edge.id)
 plan = sora.plan_edge(edge.id, seed.read_text(encoding="utf-8") if seed else "")
 Presentation.show_plan(plan)

 contract = Contract.desde_plan_sora(edge, plan)
 contract.guardar(edge.ruta_contrato)

 print("\n¿Aprobar el plan y continuar?")
 verdict = Presentation.ask_verdict()
 state = {
     "edge_id": edge.id,
     "action_details": plan,
     "tet_feedback": verdict,
     "current_step": "tet_approve",
 }
 decision, state = solicitar_aprobacion_tet(state)

 if decision == "proceed":
     edge.actualizar_estado(estado="EN_PROCESO")
     ElkiaRegistry().actualizar(edge.id, estado="EN_PROCESO")
     print("✔ Plan aprobado. Edge en proceso.")
     return 0
 if decision == "rollback":
     edge.actualizar_estado(estado="EN_REVISION")
     print("✖ Plan rechazado. Edge en revisión.")
     return 1
 # decision == "modify"
 print("➜ Observaciones registradas. Edge en revisión.")
 edge.actualizar_estado(estado="EN_REVISION")
 return 1


def continue_edge(edge_id: str) -> int:
 """Continúa un edge existente mostrando el estado actual."""
 edge = Edge.cargar(edge_id)
 print(f"\n✔ Edge: {edge.id} ({edge.titulo})")
 print(f"  Estado: {edge.estado}")
 print(f"  Avance: {edge.avance}%")
 print(f"  Prioridad: {edge.prioridad}")
 print(f"  Contrato: {edge.ruta_contrato}")
 return 0


def approve(edge_id: str, step: str = "final") -> int:
 """Aprueba un paso del edge con firma HITL."""
 state = {
     "edge_id": edge_id,
     "action_details": {"step": step},
     "tet_feedback": "aprobar",
     "current_step": step,
 }
 decision, state = solicitar_aprobacion_tet(state)
 if decision == "proceed":
     print(f"✔ Aprobado: {step}")
     return 0
 print(f"✖ No aprobado: {step}")
 return 1


def reject(edge_id: str, step: str = "final") -> int:
 """Rechaza un paso del edge con rollback."""
 state = {
     "edge_id": edge_id,
     "action_details": {"step": step},
     "tet_feedback": "rechazar",
     "current_step": step,
 }
 decision, state = solicitar_aprobacion_tet(state)
 if decision == "rollback":
     print(f"✖ Rechazado con rollback: {step}")
     return 0
 print(f"➜ Rechazo registrado: {step}")
 return 1
