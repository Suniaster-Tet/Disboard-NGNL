"""Persistencia y transiciones HITL del flujo operativo web."""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.chlammy.agent import ChlammyAuditor
from agents.jibril.agent import JibrilScientific
from agents.shiro.agent import ShiroAnalyst
from agents.sora.agent import SoraStrategist
from core.artifact import Artifact
from core.contract import Contract
from core.edge import Edge
from core.hitl import firmar_aprobacion, verificar_firma_tet
from core.log import Log
from elkia.registry import ElkiaRegistry


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _initial_state() -> dict[str, Any]:
    return {
        "requests": [],
        "bibliography": [],
        "plan": None,
        "plan_approved": False,
        "deliverables": [],
        "artifacts": {},
        "final": {"status": "pending", "observations": ""},
    }


class EdgeWorkflow:
    """Coordina solicitudes, plan, bibliografía, entregables y veredictos de Tet."""

    def __init__(self, edge: Edge):
        self.edge = edge
        self.path = edge.ruta / "workflow.json"
        self.log = Log(edge.id, ruta=edge.ruta_log)
        if not self.path.exists():
            self.state = _initial_state()
            self._save()
        else:
            self.state = json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        temp_path = self.path.with_suffix(".json.tmp")
        temp_path.write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        temp_path.replace(self.path)

    def _sign(self, action: str, details: dict[str, Any]) -> dict[str, str]:
        payload = json.loads(
            json.dumps({"edge_id": self.edge.id, "action": action, **details}, ensure_ascii=False)
        )
        return firmar_aprobacion(payload)

    def _verify_signature(self, action: str, details: dict[str, Any], approval: Any) -> bool:
        if not isinstance(approval, dict) or not isinstance(approval.get("payload"), dict):
            return False
        expected = {"edge_id": self.edge.id, "action": action, **details}
        payload = approval["payload"]
        return payload == expected and verificar_firma_tet(
            payload, str(approval.get("firma", ""))
        )

    def _require_plan_approval(self) -> None:
        plan = self.state.get("plan")
        if not self.state.get("plan_approved") or not plan or not self._verify_signature(
            "plan_approved", {"plan": plan}, self.state.get("plan_approval")
        ):
            raise ValueError("La aprobación firmada del plan falta o no coincide; Tet debe aprobarlo de nuevo.")

    def _approved_references(self) -> list[dict[str, Any]]:
        approved = []
        for item in self.state["bibliography"]:
            if item["status"] != "approved":
                continue
            if not self._verify_signature(
                "bibliography_approved",
                {"doi": item["doi"], "metadata": item["metadata"]},
                item.get("approval"),
            ):
                raise ValueError(f"La autorización de Tet para {item['doi']} falta o no coincide.")
            approved.append(item["metadata"])
        return approved

    def _verified_deliverable_hashes(self, deliverable_id: str) -> list[str]:
        records = [
            record for record in self.state["artifacts"].get(deliverable_id, [])
            if record.get("status") != "rejected"
        ]
        artifact_root = (self.edge.ruta / "artifacts").resolve()
        hashes = []
        for record in records:
            path = Path(record["path"]).resolve()
            if not path.is_relative_to(artifact_root) or not path.is_file():
                raise ValueError(f"Falta el artefacto aprobado {record.get('name', '?')}.")
            artifact = Artifact(
                edge_id=self.edge.id,
                name=record["name"],
                path=path,
                agent=record["agent"],
                sha256=record["sha256"],
            )
            if not artifact.verify():
                raise ValueError(f"El hash de {record['name']} no coincide; Tet debe revisarlo.")
            hashes.append(record["sha256"])
        if not hashes:
            raise ValueError(f"El entregable {deliverable_id} no tiene artefactos activos.")
        return sorted(hashes)

    def _final_approval_is_valid(self) -> bool:
        final = self.state.get("final", {})
        if final.get("status") != "approved":
            return False
        try:
            self._require_plan_approval()
            approvals = {}
            for item in self.state["deliverables"]:
                hashes = self._verified_deliverable_hashes(item["id"])
                if not self._verify_signature(
                    "deliverable_approved",
                    {"deliverable_id": item["id"], "artifact_hashes": hashes},
                    item.get("approval"),
                ):
                    return False
                approvals[item["id"]] = item["approval"]["firma"]
            return self._verify_signature(
                "edge_completed",
                {
                    "deliverables": [item["id"] for item in self.state["deliverables"]],
                    "approvals": approvals,
                },
                final.get("approval"),
            )
        except (KeyError, RuntimeError, ValueError):
            return False

    def add_request(self, text: str) -> dict[str, Any]:
        text = text.strip()
        if not text:
            raise ValueError("La solicitud de Tet no puede estar vacía.")
        request = {"text": text, "created_at": _utcnow(), "status": "pending"}
        self.state["requests"].append(request)
        self.state["final"] = {"status": "pending", "observations": ""}
        self.log.registrar("tet_request_received", request, agente="Tet")
        self._save()
        return request

    def generate_plan(self, request_text: str | None = None) -> dict[str, Any]:
        text = request_text or (
            self.state["requests"][-1]["text"] if self.state["requests"]
            else self.edge.ruta_seed.read_text(encoding="utf-8")
            if self.edge.ruta_seed.exists() else ""
        )
        if not text.strip():
            raise ValueError("Añade una solicitud de Tet antes de generar el plan.")
        approved_refs = self._approved_references()
        plan = SoraStrategist(edge_id=self.edge.id).plan_edge(
            self.edge.id, text, bibliography=approved_refs
        )
        self.state["plan"] = plan
        self.state["deliverables"] = [
            {**item, "estado": "pendiente", "observaciones": ""}
            for item in plan["entregables"]
        ]
        self.state["plan_approved"] = False
        Contract.desde_plan_sora(self.edge, plan).guardar(self.edge.ruta_contrato)
        self.log.registrar(
            "sora_plan_proposed",
            {"objectives": plan["objetivos"], "deliverables": len(plan["entregables"]),
             "approved_references": [ref.get("doi") for ref in approved_refs]},
            agente="Sora",
        )
        self._save()
        return self.snapshot()

    def approve_plan(self, edits: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.state["plan"]:
            raise ValueError("Sora aún no ha propuesto un plan.")
        edits = edits or {}
        plan = dict(self.state["plan"])
        for field in ("objetivos", "metas", "entregables"):
            if field in edits:
                plan[field] = edits[field]
        if not plan["objetivos"] or not plan["metas"] or not plan["entregables"]:
            raise ValueError("El plan requiere objetivos, metas y entregables.")
        deliverables = []
        for item in plan["entregables"]:
            if not item.get("id") or not item.get("descripcion"):
                raise ValueError("Cada entregable requiere id y descripción.")
            deliverables.append({**item, "estado": "pendiente", "observaciones": ""})
        plan["entregables"] = deliverables
        contract = Contract.desde_plan_sora(self.edge, plan)
        contract.validate_errors = contract.validar()
        if contract.validate_errors:
            raise ValueError("; ".join(contract.validate_errors))
        signature = self._sign("plan_approved", {"plan": plan})
        contract.aprobar(signature["firma"])
        contract.guardar(self.edge.ruta_contrato)
        self.state["plan"] = json.loads(json.dumps(plan, ensure_ascii=False))
        self.state["deliverables"] = json.loads(json.dumps(deliverables, ensure_ascii=False))
        self.state["plan_approved"] = True
        self.state["plan_approval"] = signature
        for request in self.state["requests"]:
            request["status"] = "planned"
        self.log.registrar(
            "plan_approved",
            {"signature": signature["firma"], "approved_at": signature["ts"]},
            agente="Tet",
        )
        sora_item = next(
            (item for item in self.state["deliverables"] if item.get("agente_asignado") == "Sora"),
            None,
        )
        if sora_item:
            artifact = Artifact.register(
                self.edge,
                self.edge.ruta_contrato,
                agent="Sora",
                target_relative="contract.md",
                metadata={"deliverable_id": sora_item["id"]},
            )
            sora_item["estado"] = "aprobado"
            sora_item["approval"] = self._sign(
                "deliverable_approved",
                {"deliverable_id": sora_item["id"], "artifact_hashes": [artifact.sha256]},
            )
            self.state["artifacts"][sora_item["id"]] = [artifact.to_dict()]
        self._save()
        self._refresh_edge()
        return self.snapshot()

    def add_reference(self, doi: str, metadata: dict[str, Any], proposer: str) -> dict[str, Any]:
        doi = doi.strip().lower()
        if not doi or not metadata:
            raise ValueError("La referencia requiere DOI verificado y metadatos.")
        existing = next(
            (item for item in self.state["bibliography"] if item["doi"] == doi), None
        )
        if existing:
            return existing
        candidate = {
            "doi": doi,
            "metadata": metadata,
            "proposer": proposer,
            "status": "pending_approval",
            "created_at": _utcnow(),
        }
        self.state["bibliography"].append(candidate)
        self.log.registrar("bibliography_verified_proposed", candidate, agente="Jibril")
        self._save()
        return candidate

    def review_reference(self, doi: str, verdict: str) -> dict[str, Any]:
        item = next((ref for ref in self.state["bibliography"] if ref["doi"] == doi.lower()), None)
        if not item:
            raise KeyError(f"DOI no encontrado: {doi}")
        if verdict == "approve":
            signature = self._sign(
                "bibliography_approved",
                {"doi": item["doi"], "metadata": item["metadata"]},
            )
            item.update(status="approved", approval=signature)
            event = "bibliography_approved"
        elif verdict == "reject":
            item.update(status="rejected", rejected_at=_utcnow())
            event = "bibliography_rejected"
        else:
            raise ValueError("Veredicto inválido para una referencia.")
        self.log.registrar(event, {"doi": item["doi"]}, agente="Tet")
        self._save()
        return item

    def execute_deliverable(self, deliverable_id: str) -> dict[str, Any]:
        self._require_plan_approval()
        item = self._deliverable(deliverable_id)
        agent = item.get("agente_asignado", "Shiro")
        created: list[Artifact] = []
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            if agent == "Jibril":
                references = self._approved_references()
                if not references:
                    raise ValueError("Tet debe autorizar al menos una referencia verificada.")
                content = JibrilScientific(edge_id=self.edge.id).export_bibtex(references)
                source = temp_root / "bibliography.bib"
                source.write_text(content, encoding="utf-8")
                created.append(self._register_artifact(source, item, agent))
            elif agent == "Shiro":
                code, test_code = ShiroAnalyst(edge_id=self.edge.id).generate_tdd_code(
                    item["descripcion"]
                )
                safe_id = "".join(c if c.isalnum() or c in "- _" else "_" for c in deliverable_id)
                for filename, content in ((f"{safe_id}.py", code), (f"{safe_id}_test.py", test_code)):
                    source = temp_root / filename
                    source.write_text(content, encoding="utf-8")
                    created.append(self._register_artifact(source, item, agent))
            elif agent in {"Chlammy", "Chlammy Zell"}:
                contract = Contract.desde_plan_sora(self.edge, self.state["plan"])
                result = ChlammyAuditor(edge_id=self.edge.id).verify_contract_alignment(
                    contract.to_dict(), self.state["deliverables"]
                )
                source = temp_root / "audit.json"
                source.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
                created.append(self._register_artifact(source, item, agent))
                item["audit"] = result
            else:
                raise ValueError(f"No hay ejecutor web implementado para {agent}.")
        item["estado"] = "entregado"
        item["entregado_en"] = _utcnow()
        self.state["artifacts"].setdefault(deliverable_id, []).extend(
            artifact.to_dict() for artifact in created
        )
        self.log.registrar(
            "deliverable_submitted",
            {"deliverable_id": deliverable_id, "agent": agent,
             "artifacts": [artifact.name for artifact in created]},
            agente=agent,
        )
        self._save()
        self._refresh_edge()
        return self.snapshot()

    def submit_artifact(
        self, deliverable_id: str, source: Path, filename: str
    ) -> dict[str, Any]:
        self._require_plan_approval()
        item = self._deliverable(deliverable_id)
        artifact = Artifact.register(
            self.edge,
            source,
            agent="Tet",
            target_relative=Path(filename).name,
            metadata={"deliverable_id": deliverable_id, "uploaded_by": "Tet"},
        )
        item["estado"] = "entregado"
        item["entregado_en"] = _utcnow()
        self.state["artifacts"].setdefault(deliverable_id, []).append(artifact.to_dict())
        self.log.registrar(
            "deliverable_submitted",
            {"deliverable_id": deliverable_id, "artifact": artifact.name},
            agente="Tet",
        )
        self._save()
        self._refresh_edge()
        return self.snapshot()

    def _register_artifact(self, source: Path, deliverable: dict[str, Any], agent: str) -> Artifact:
        return Artifact.register(
            self.edge,
            source,
            agent=agent,
            metadata={"deliverable_id": deliverable["id"]},
        )

    def review_deliverable(
        self, deliverable_id: str, verdict: str, observations: str = ""
    ) -> dict[str, Any]:
        self._require_plan_approval()
        item = self._deliverable(deliverable_id)
        if verdict == "approve":
            if item["estado"] != "entregado":
                raise ValueError("El entregable no está esperando revisión.")
            hashes = self._verified_deliverable_hashes(deliverable_id)
            item["approval"] = self._sign(
                "deliverable_approved",
                {"deliverable_id": deliverable_id, "artifact_hashes": hashes},
            )
            item["estado"] = "aprobado"
            event = "deliverable_approved"
        elif verdict == "modify":
            item["estado"] = "pendiente"
            item["observaciones"] = observations.strip()
            event = "deliverable_changes_requested"
        elif verdict == "reject":
            for record in self.state["artifacts"].get(deliverable_id, []):
                path = Path(record["path"]).resolve()
                root = (self.edge.ruta / "artifacts").resolve()
                if path.is_relative_to(root) and path.is_file():
                    path.unlink()
                    self.log.registrar(
                        "artifact_deleted",
                        {"name": record["name"], "reason": observations or "rechazo de Tet"},
                        agente=record["agent"],
                    )
                record["status"] = "rejected"
                record["deleted_at"] = _utcnow()
            item["estado"] = "rechazado"
            item["observaciones"] = observations.strip()
            event = "deliverable_rejected"
        else:
            raise ValueError("Veredicto inválido para un entregable.")
        self.log.registrar(
            event,
            {"deliverable_id": deliverable_id, "observations": observations.strip()},
            agente="Tet",
        )
        self._save()
        self._refresh_edge()
        return self.snapshot()

    def decide_final(self, verdict: str, observations: str = "") -> dict[str, Any]:
        if verdict == "approve":
            self._require_plan_approval()
            pending = [item["id"] for item in self.state["deliverables"] if item["estado"] != "aprobado"]
            if pending:
                raise ValueError(f"Entregables sin aprobar: {', '.join(pending)}")
            approvals = {}
            for item in self.state["deliverables"]:
                hashes = self._verified_deliverable_hashes(item["id"])
                if not self._verify_signature(
                    "deliverable_approved",
                    {"deliverable_id": item["id"], "artifact_hashes": hashes},
                    item.get("approval"),
                ):
                    raise ValueError(f"La aprobación de {item['id']} falta o no coincide.")
                approvals[item["id"]] = item["approval"]["firma"]
            signature = self._sign(
                "edge_completed",
                {"deliverables": [item["id"] for item in self.state["deliverables"]],
                 "approvals": approvals},
            )
            self.state["final"] = {"status": "approved", "approval": signature, "observations": ""}
            self.log.registrar("edge_completed", {"signature": signature["firma"]}, agente="Tet")
        elif verdict in {"modify", "reject"}:
            self.state["final"] = {
                "status": "revision" if verdict == "modify" else "rejected",
                "observations": observations.strip(),
                "updated_at": _utcnow(),
            }
            self.log.registrar(
                "final_changes_requested" if verdict == "modify" else "edge_rejected",
                {"observations": observations.strip()},
                agente="Tet",
            )
        else:
            raise ValueError("Veredicto final inválido.")
        self._save()
        self._refresh_edge()
        return self.snapshot()

    def _deliverable(self, deliverable_id: str) -> dict[str, Any]:
        item = next(
            (entry for entry in self.state["deliverables"] if entry["id"] == deliverable_id),
            None,
        )
        if not item:
            raise KeyError(f"Entregable no encontrado: {deliverable_id}")
        return item

    def _refresh_edge(self) -> None:
        deliverables = self.state["deliverables"]
        approved = sum(item["estado"] == "aprobado" for item in deliverables)
        progress = round(approved / len(deliverables) * 100) if deliverables else 0
        if self._final_approval_is_valid():
            status = "COMPLETO"
        elif self.state["plan_approved"]:
            status = "EN_PROCESO"
        elif self.state["plan"]:
            status = "EN_REVISION"
        else:
            status = "NUEVO"
        self.edge.actualizar_estado(
            avance=progress,
            prioridad=self.state.get("plan", {}).get("prioridad", self.edge.prioridad),
            estado=status,
        )
        registry = ElkiaRegistry()
        if registry.existe(self.edge.id):
            registry.actualizar(
                self.edge.id, avance=progress, prioridad=self.edge.prioridad, estado=status
            )

    def snapshot(self) -> dict[str, Any]:
        state = json.loads(json.dumps(self.state, ensure_ascii=False, default=str))
        if state["final"]["status"] == "approved" and not self._final_approval_is_valid():
            state["final"]["status"] = "invalid"
        return state