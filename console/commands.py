"""Comandos de la consola HITL (start, continue, approve, reject)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from agents.jibril.agent import JibrilScientific
from console.presentation import Presentation
from core.edge import Edge
from core.log import Log
from elkia.registry import ElkiaRegistry
from web.workflow import EdgeWorkflow


def start(seed: Optional[Path], title: Optional[str] = None) -> int:
 """Inicia el mismo workflow HITL que usa el dashboard."""
 if seed and not seed.exists():
     print(f"✖ No se encontró la semilla: {seed}")
     return 2

 edge = Edge.crear_desde_semilla(seed, titulo=title)
 workflow = EdgeWorkflow(edge)
 Log(edge.id, ruta=edge.ruta_log).registrar("edge_created", {"seed": str(seed) if seed else None}, agente="Tet")
 ElkiaRegistry().registrar(edge)

 print(f"\n✔ Edge creado: {edge.id}")
 print(f"➜ Ruta: {edge.ruta}")
 request = seed.read_text(encoding="utf-8") if seed else input("Solicitud libre para Sora: ").strip()
 workflow.add_request(request)
 state = workflow.generate_plan()
 while True:
     Presentation.show_plan(state["plan"])
     print("\n¿Aprobar el plan y continuar?")
     verdict = Presentation.ask_verdict()
     if verdict == "aprobar":
         workflow.approve_plan()
         print("✔ Plan aprobado y firmado. Puedes continuar con `disboard work` o desde el dashboard.")
         return 0
     observations = Presentation.ask_observations()
     if verdict == "rechazar":
         workflow.decide_final("reject", observations)
         print("✖ Plan rechazado. La decisión quedó registrada.")
         return 1
     workflow.add_request(f"Modificar el plan: {observations}")
     state = workflow.generate_plan()


def continue_edge(edge_id: str) -> int:
 """Continúa un edge existente mostrando el estado actual."""
 edge = Edge.cargar(edge_id)
 print(f"\n✔ Edge: {edge.id} ({edge.titulo})")
 print(f"  Estado: {edge.estado}")
 print(f"  Avance: {edge.avance}%")
 print(f"  Prioridad: {edge.prioridad}")
 print(f"  Contrato: {edge.ruta_contrato}")
 workflow = EdgeWorkflow(edge)
 state = workflow.snapshot()
 print(f"  Plan: {'aprobado' if state['plan_approved'] else 'pendiente' if state['plan'] else 'sin generar'}")
 print(f"  Referencias: {len(state['bibliography'])}")
 print(f"  Entregables: {len(state['deliverables'])}")
 print(f"  Workflow: {edge.ruta / 'workflow.json'}")
 print("  Usa `disboard work" + f" {edge_id}` para continuar interactuando.")
 return 0


def approve(edge_id: str, step: str = "final") -> int:
 """Aprueba plan, entregable o cierre usando el workflow compartido."""
 workflow = EdgeWorkflow(Edge.cargar(edge_id))
 if step == "plan":
     workflow.approve_plan()
 elif step == "final":
     workflow.decide_final("approve")
 else:
     workflow.review_deliverable(step, "approve")
 print(f"✔ Aprobado y firmado: {step}")
 return 0


def reject(edge_id: str, step: str = "final") -> int:
 """Rechaza plan, entregable o edge usando el workflow compartido."""
 workflow = EdgeWorkflow(Edge.cargar(edge_id))
 observations = Presentation.ask_observations()
 if step == "plan":
     workflow.decide_final("reject", observations)
 elif step == "final":
     workflow.decide_final("reject", observations)
 else:
     workflow.review_deliverable(step, "reject", observations)
 print(f"✖ Rechazo registrado: {step}")
 return 0


def work(edge_id: str) -> int:
 """Abre un menú interactivo sobre el workflow compartido con el dashboard."""
 workflow = EdgeWorkflow(Edge.cargar(edge_id))
 actions = {
     "1": "Nueva solicitud directa",
     "2": "Generar o actualizar plan de Sora",
     "3": "Aprobar plan",
     "4": "Buscar bibliografía con Jibril",
     "5": "Verificar DOI proporcionado por Tet",
     "6": "Decidir sobre una referencia",
     "7": "Ejecutar entregable",
     "8": "Adjuntar archivo a un entregable",
     "9": "Revisar entregable",
     "10": "Decidir cierre final",
     "0": "Salir",
 }
 while True:
     print(f"\n{edge_id} | {workflow.edge.estado} | {workflow.edge.avance}%")
     for key, label in actions.items():
         print(f"  {key}) {label}")
     choice = input("➜ ").strip()
     try:
         if choice == "0":
             return 0
         if choice == "1":
             workflow.add_request(input("Solicitud para Tet/Sora: "))
             workflow.generate_plan()
         elif choice == "2":
             workflow.generate_plan()
         elif choice == "3":
             workflow.approve_plan()
         elif choice == "4":
             query = input("Tema de búsqueda: ").strip()
             jibril = JibrilScientific(edge_id=edge_id)
             suggestions = jibril.search_references(query)
             for reference in suggestions:
                 workflow.add_reference(reference["doi"], reference, proposer="Jibril")
                 print(f"  {reference['doi']} | {reference.get('title', 'Sin título')}")
         elif choice == "5":
             doi = input("DOI: ").strip()
             result = JibrilScientific(edge_id=edge_id).verify_reference(doi)
             if not result["ok"]:
                 raise ValueError(result["reason"])
             workflow.add_reference(doi, result["metadata"], proposer="Tet")
         elif choice == "6":
             doi = input("DOI: ").strip()
             verdict = Presentation.ask_verdict()
             workflow.review_reference(doi, "approve" if verdict == "aprobar" else "reject")
         elif choice == "7":
             deliverable_id = input("ID del entregable: ").strip()
             workflow.execute_deliverable(deliverable_id)
         elif choice == "8":
             deliverable_id = input("ID del entregable: ").strip()
             source = Path(input("Ruta del archivo: ").strip()).expanduser()
             if not source.is_file():
                 raise ValueError(f"No se encontró el archivo: {source}")
             workflow.submit_artifact(deliverable_id, source, source.name)
         elif choice == "9":
             deliverable_id = input("ID del entregable: ").strip()
             verdict = Presentation.ask_verdict()
             observations = Presentation.ask_observations() if verdict != "aprobar" else ""
             decision = {"aprobar": "approve", "modificar": "modify", "rechazar": "reject"}[verdict]
             workflow.review_deliverable(deliverable_id, decision, observations)
         elif choice == "10":
             verdict = Presentation.ask_verdict()
             observations = Presentation.ask_observations() if verdict != "aprobar" else ""
             decision = {"aprobar": "approve", "modificar": "modify", "rechazar": "reject"}[verdict]
             workflow.decide_final(decision, observations)
         else:
             print("Opción no válida.")
             continue
         workflow = EdgeWorkflow(Edge.cargar(edge_id))
         print("✔ Workflow actualizado; el dashboard verá los mismos cambios.")
     except (KeyError, RuntimeError, ValueError) as error:
         print(f"✖ {error}")
