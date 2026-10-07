#!/usr/bin/env python3
"""A local-only, checkpointed multi-agent workflow for the Disboard web app."""
import json
import os
import re
from pathlib import Path
from typing import TypedDict

from kuhaku_governance import KuhakuGovernance
from disboard_skills import cargar_skill
from disboard_registry import (
    agent_index_context,
    project_by_slug,
    read_master_index,
    update_project,
)


class DisboardState(TypedDict, total=False):
    run_id: str
    task: str
    project: str
    master_context: str
    plan: str
    references: str
    draft: str
    review: str
    approved: bool
    revisions: int
    trace: list


class DisboardAgentGraph:
    def __init__(self, root_dir, governance=None):
        self.root_dir = Path(root_dir).resolve()
        self.governance = governance or KuhakuGovernance(self.root_dir)
        data_dir = Path(os.environ.get("DISBOARD_DATA_DIR", ".disboard-local")).expanduser()
        data_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            data_dir.chmod(0o700)
        except OSError:
            pass
        self.checkpoint_path = data_dir / "agent-checkpoints.sqlite3"
        descriptor = os.open(self.checkpoint_path, os.O_CREAT | os.O_RDWR, 0o600)
        os.close(descriptor)
        try:
            self.checkpoint_path.chmod(0o600)
        except OSError:
            pass

    def _consultar(self, agente, prompt):
        respuesta, _ = self.governance.consultar_ia(
            agente,
            prompt,
            proveedor_preferido="ollama",
            solo_local=True,
        )
        if self.governance._es_error_de_inferencia(respuesta):
            raise RuntimeError(respuesta)
        return respuesta

    def _cargar_skill(self, agente):
        return cargar_skill(self.root_dir, agente)

    def _contexto_proyecto(self, slug):
        index = read_master_index(self.root_dir / "Elkia.md")
        global_context = agent_index_context(index)
        if not slug:
            return "Lectura inicial de Elkia.md:\n" + global_context
        if not re.fullmatch(r"edge-[A-Za-z0-9_-]+", slug):
            raise ValueError("El slug de proyecto no es válido.")
        if not project_by_slug(index, slug):
            raise ValueError(f"El edge no está registrado en Elkia.md: {slug}")
        project_dir = (self.root_dir / slug).resolve()
        if project_dir.parent != self.root_dir or not (project_dir / "contract.md").is_file():
            raise ValueError("El proyecto seleccionado no tiene contract.md.")
        contract = (project_dir / "contract.md").read_text(encoding="utf-8")[:8000]
        return (
            "Lectura inicial de Elkia.md:\n" + global_context
            + "\n\nContrato del proyecto, leído después de Elkia.md:\n" + contract
        )

    def _notas_bibliograficas(self, slug):
        if not slug:
            return ""
        project_dir = (self.root_dir / slug).resolve()
        if project_dir.parent != self.root_dir:
            raise ValueError("El proyecto seleccionado sale de la raíz del repositorio.")
        notes_dir = project_dir / "docs" / "bibliografia"
        chunks = []
        remaining = 12000
        if notes_dir.is_dir():
            for note in sorted(notes_dir.glob("*.md")):
                if note.is_symlink() or not note.is_file() or remaining <= 0:
                    continue
                text = note.read_text(encoding="utf-8")[:remaining]
                chunks.append(f"Nota bibliográfica local ({note.name}):\n{text}")
                remaining -= len(text)
        return "\n\n".join(chunks)

    def _build_graph(self):
        from langgraph.graph import END, START, StateGraph

        builder = StateGraph(DisboardState)
        builder.add_node("sora_plan", self._planificar)
        builder.add_node("jibril_sources", self._sintetizar_bibliografia)
        builder.add_node("shiro_execute", self._ejecutar)
        builder.add_node("kurami_review", self._revisar)
        builder.add_node("shiro_revise", self._corregir)
        builder.add_edge(START, "sora_plan")
        builder.add_conditional_edges(
            "sora_plan",
            self._ruta_bibliografia,
            {"jibril": "jibril_sources", "execute": "shiro_execute"},
        )
        builder.add_edge("jibril_sources", "shiro_execute")
        builder.add_edge("shiro_execute", "kurami_review")
        builder.add_conditional_edges(
            "kurami_review",
            self._ruta_revision,
            {"revise": "shiro_revise", "finish": END},
        )
        builder.add_edge("shiro_revise", "kurami_review")
        return builder

    def _planificar(self, state):
        proyecto = state.get("project") or "sin proyecto seleccionado"
        project_context = self._contexto_proyecto(state.get("project", ""))
        master_context = project_context.split(
            "\n\nContrato del proyecto, leído después de Elkia.md:", 1
        )[0]
        plan = self._consultar(
            "Sora",
            "Lee primero las reglas, roles y registro de Elkia.md que se proporcionan; "
            "después consulta el contrato del edge seleccionado. Planifica esta solicitud "
            "en pasos verificables. No inventes datos ausentes; "
            f"señala supuestos y riesgos. Proyecto: {proyecto}\nSolicitud: {state['task']}"
            f"\n\nContexto local autorizado:\n{project_context}"
            f"\n\nSkill de Sora:\n{self._cargar_skill('Sora')[:3000]}",
        )
        return {
            "plan": plan,
            "master_context": master_context,
            "trace": state.get("trace", []) + [{"agent": "Sora", "stage": "Planificación", "status": "Completado"}],
        }

    def _ruta_bibliografia(self, state):
        return "jibril" if self._notas_bibliograficas(state.get("project", "")) else "execute"

    def _sintetizar_bibliografia(self, state):
        notes = self._notas_bibliograficas(state.get("project", ""))
        synthesis = self._consultar(
            "Jibril",
            "Lee primero el registro global de Elkia.md; después analiza únicamente "
            "estas notas bibliográficas locales para la solicitud. "
            "Devuelve hallazgos relevantes, DOI/páginas citados, límites y qué dato no está "
            "disponible. No inventes referencias ni añadas fuentes.\nSolicitud: " + state["task"] +
            "\nElkia.md:\n" + state.get("master_context", "") +
            "\nPlan de Sora:\n" + state["plan"] + "\nNotas:\n" + notes +
            "\n\nSkill de Jibril:\n" + self._cargar_skill("Jibril")[:3000],
        )
        return {
            "references": synthesis,
            "trace": state.get("trace", []) + [{"agent": "Jibril", "stage": "Síntesis bibliográfica local", "status": "Completado"}],
        }

    def _ejecutar(self, state):
        draft = self._consultar(
            "Shiro",
            "Lee primero el registro global de Elkia.md y luego resuelve la tarea "
            "usando el plan de Sora. Produce una respuesta concreta y "
            "declara cualquier incertidumbre.\nSolicitud: " + state["task"] +
            "\nElkia.md:\n" + state.get("master_context", "") +
            "\nPlan de Sora:\n" + state["plan"] +
            "\nNotas de Jibril:\n" + state.get("references", "Sin notas bibliográficas locales.") +
            "\n\nSkill de Shiro:\n" + self._cargar_skill("Shiro")[:3000],
        )
        return {
            "draft": draft,
            "revisions": 0,
            "trace": state.get("trace", []) + [{"agent": "Shiro", "stage": "Ejecución", "status": "Completado"}],
        }

    def _revisar(self, state):
        raw_review = self._consultar(
            "Kurami Zell",
            "Lee primero el registro global de Elkia.md y audita críticamente el "
            "borrador respecto a la solicitud y el plan. "
            "Responde solo JSON válido con las claves approved (boolean) y feedback (string). "
            "Aprueba únicamente si no detectas errores materiales.\nSolicitud: " + state["task"] +
            "\nElkia.md:\n" + state.get("master_context", "") +
            "\nPlan:\n" + state["plan"] + "\nBorrador:\n" + state["draft"] +
            "\n\nSkill de Kurami Zell:\n" + self._cargar_skill("Kurami Zell")[:3000],
        )
        match = re.search(r"\{.*\}", raw_review, flags=re.DOTALL)
        try:
            parsed = json.loads(match.group(0)) if match else {}
        except json.JSONDecodeError:
            parsed = {}
        approved = parsed.get("approved") is True
        feedback = str(parsed.get("feedback", raw_review)).strip()
        return {
            "approved": approved,
            "review": feedback,
            "trace": state.get("trace", []) + [{
                "agent": "Kurami Zell",
                "stage": "Revisión independiente",
                "status": "Aprobado" if approved else "Solicita corrección",
            }],
        }

    def _corregir(self, state):
        draft = self._consultar(
            "Shiro",
            "Lee primero el registro global de Elkia.md y corrige tu respuesta atendiendo "
            "la auditoría de Kurami. Si una observación "
            "no aplica, explica brevemente por qué en el resultado.\nSolicitud: " + state["task"] +
            "\nElkia.md:\n" + state.get("master_context", "") +
            "\nBorrador anterior:\n" + state["draft"] + "\nAuditoría:\n" + state["review"] +
            "\n\nSkill de Shiro:\n" + self._cargar_skill("Shiro")[:3000],
        )
        return {
            "draft": draft,
            "revisions": state.get("revisions", 0) + 1,
            "trace": state.get("trace", []) + [{"agent": "Shiro", "stage": "Corrección", "status": "Completado"}],
        }

    @staticmethod
    def _ruta_revision(state):
        if state.get("approved") or state.get("revisions", 0) >= 1:
            return "finish"
        return "revise"

    def run(self, task, project=""):
        from langgraph.checkpoint.sqlite import SqliteSaver

        if project:
            update_project(
                self.root_dir / "Elkia.md",
                project,
                status="EN_PROCESO",
                milestone="Tet inició una ejecución del grafo LangGraph",
                next_action="Revisar la respuesta del grafo y decidir el siguiente paso",
            )
        config = {"configurable": {"thread_id": os.urandom(16).hex()}}
        with SqliteSaver.from_conn_string(str(self.checkpoint_path)) as checkpointer:
            graph = self._build_graph().compile(checkpointer=checkpointer)
            result = graph.invoke(
                {"task": task, "project": project, "revisions": 0},
                config=config,
            )
        if project:
            update_project(
                self.root_dir / "Elkia.md",
                project,
                status="EN_PROCESO",
                milestone="LangGraph produjo una respuesta pendiente de aprobación humana",
                next_action="Tet: revisar plan, borrador y crítica antes de reutilizar",
                responsible="Tet",
            )
        return {
            "run_id": config["configurable"]["thread_id"],
            "plan": result.get("plan", ""),
            "draft": result.get("draft", ""),
            "review": result.get("review", ""),
            "approved_by_agent": result.get("approved", False),
            "revisions": result.get("revisions", 0),
            "trace": result.get("trace", []),
            "human_approval_required": True,
        }