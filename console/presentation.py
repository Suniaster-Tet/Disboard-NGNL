"""Presentación de artefactos y veredictos HITL de Tet."""
from __future__ import annotations

from typing import Any, Dict, List

from core.artifact import Artifact


class Presentation:
 """Presenta artefactos a Tet y recoge su veredicto."""

 @staticmethod
 def show_artifact(artifact: Artifact) -> None:
     print(f"\n➜ Artefacto: {artifact.nombre}")
     print(f"  Ruta: {artifact.ruta}")
     print(f"  Agente: {artifact.agente}")
     print(f"  SHA-256: {artifact.sha256[:16]}...")
     print(f"  Creado: {artifact.creado_en}")

 @staticmethod
 def show_plan(plan: Dict[str, Any]) -> None:
     print("\n# Plan de Sora")
     print("## Objetivos")
     for o in plan.get("objetivos", []):
         print(f"  - {o}")
     print("## Metas")
     for m in plan.get("metas", []):
         print(f"  - {m}")
     print("## Entregables")
     for e in plan.get("entregables", []):
         print(
             f"  - [{e.get('id', '?')}] {e.get('descripcion', '')} "
             f"→ {e.get('agente_asignado', '?')}"
         )

 @staticmethod
 def show_status(edges: List[Any]) -> None:
     if not edges:
         print("✔ No hay partidas activas. Matriz de Eisenhower en equilibrio.")
         return
     print(f"➜ {len(edges)} edge(s) activo(s):")
     for e in edges:
         print(
             f"  - {e.id} | avance: {e.avance:>3}% | "
             f"prioridad: {e.prioridad} | estado: {e.estado}"
         )

 @staticmethod
 def show_dashboard(markdown: str) -> None:
     print(markdown)

 @staticmethod
 def ask_verdict() -> str:
     print("\n¿Veredicto de Tet?")
     print("  1) Aprobar")
     print("  2) Modificar")
     print("  3) Rechazar")
     while True:
         opcion = input("➜ ").strip().lower()
         if opcion in {"1", "aprobar", "aprobado"}:
             return "aprobar"
         if opcion in {"2", "modificar"}:
             return "modificar"
         if opcion in {"3", "rechazar", "rechazado"}:
             return "rechazar"
         print("Opción no válida. Intenta de nuevo.")

 @staticmethod
 def ask_observations() -> str:
     return input("Observaciones para el agente: ").strip()
