"""Jibril — Descubrimiento Científico."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.base import Agent
from agents.jibril.crossref_client import CrossrefClient
from agents.jibril.doi_verifier import verify_doi
from agents.jibril.openalex_client import OpenAlexClient
from agents.jibril.orcid_client import OrcidClient
from core.log import Log
from core.state_schema import OverallState


class JibrilScientific(Agent):
    nombre = "Jibril"
    rol = "Descubrimiento científico / Subagente de Sora"

    def __init__(self, edge_id: Optional[str] = None):
        super().__init__(edge_id)
        self.crossref = CrossrefClient()
        self.openalex = OpenAlexClient()
        self.orcid = OrcidClient()

    # ------------------------------------------------------------------ #
    # Verificación de DOIs
    # ------------------------------------------------------------------ #
    def fetch_doi_metadata(self, doi: str) -> Dict[str, Any]:
        result = verify_doi(doi, self.crossref, self.openalex, self.orcid)
        if not result["ok"]:
            return {"doi": doi, "error": result["reason"]}
        return result["metadata"]

    def fetch_many(self, dois: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Verifica una lista de DOIs y separa aceptados de rechazados."""
        ok: List[Dict[str, Any]] = []
        rejected: List[Dict[str, Any]] = []
        for doi in dois:
            res = verify_doi(doi, self.crossref, self.openalex, self.orcid)
            if res["ok"]:
                ok.append(res["metadata"])
            else:
                rejected.append({"doi": doi, "reason": res["reason"]})
        return {"ok": ok, "rejected": rejected}

    # ------------------------------------------------------------------ #
    # BibTeX
    # ------------------------------------------------------------------ #
    def generate_bibtex_entry(self, metadata: Dict[str, Any]) -> str:
        bib_id = metadata.get("doi", "ref1").replace("/", "_").replace(".", "_")
        authors = " and ".join(metadata.get("authors", []))
        return (
            f"@article{{{bib_id},\n"
            f"  author = {{{authors}}},\n"
            f"  title = {{{metadata.get('title', '')}}},\n"
            f"  journal = {{{metadata.get('journal', '')}}},\n"
            f"  year = {{{metadata.get('year', '')}}},\n"
            f"  doi = {{{metadata.get('doi', '')}}}\n"
            f"}}"
        )

    def export_bibtex(self, metadatas: List[Dict[str, Any]]) -> str:
        return "\n\n".join(self.generate_bibtex_entry(m) for m in metadatas)

    # ------------------------------------------------------------------ #
    # Reservorio (proposals, no activos)
    # ------------------------------------------------------------------ #
    def enrich_reservoir(
        self, metadatas: List[Dict[str, Any]]
    ) -> Optional[Path]:
        """Guarda propuestas en `edges/<id>/docs/bibliography/proposals/`."""
        if not self.edge_id:
            return None
        folder = Path("edges") / self.edge_id / "docs" / "bibliography" / "proposals"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "proposals.jsonl"
        with path.open("a", encoding="utf-8") as f:
            for m in metadatas:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")
        self.register("bibliography_proposals_saved", {"n": len(metadatas)})
        return path

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #
    def execute(self, state: OverallState) -> OverallState:
        dois = state.get("action_details", {}).get("dois", [])
        result = self.fetch_many(dois)

        state["bibliography"] = state.get("bibliography", []) + result["ok"]
        state["action_details"]["jibril_rejected"] = result["rejected"]
        state["current_step"] = "shiro_execution"

        self.register(
            "bibliography_enriched",
            {"ok": len(result["ok"]), "rejected": len(result["rejected"])},
        )
        if self.edge_id:
            Log(self.edge_id).registrar(
                "bibliography_enriched",
                {"ok": len(result["ok"]), "rejected": len(result["rejected"])},
                agente=self.nombre,
            )
            self.enrich_reservoir(result["ok"])
        return state
