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

    def verify_reference(self, doi: str) -> Dict[str, Any]:
        """Verifica un DOI y devuelve metadatos uniformes con la fuente."""
        result = verify_doi(doi, self.crossref, self.openalex, self.orcid)
        if not result["ok"]:
            return result
        return {
            "ok": True,
            "source": result["source"],
            "metadata": self._normalize_metadata(doi, result["metadata"]),
        }

    def search_references(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        """Busca propuestas en Crossref; Tet debe verificarlas y autorizarlas."""
        suggestions = []
        for item in self.crossref.search(query, limit=max(1, min(limit, 20))):
            doi = item.get("DOI", "")
            result = verify_doi(doi, self.crossref, self.openalex, self.orcid)
            if result["ok"]:
                suggestions.append(
                    self._normalize_metadata(doi, result["metadata"], result["source"])
                )
        return suggestions

    @staticmethod
    def _normalize_metadata(
        doi: str, metadata: Dict[str, Any], source: str = ""
    ) -> Dict[str, Any]:
        title = metadata.get("title", "")
        if isinstance(title, list):
            title = title[0] if title else ""
        authors = metadata.get("author", [])
        if not authors and metadata.get("authorships"):
            authors = [entry.get("author", {}) for entry in metadata["authorships"]]
        normalized_authors = [
            " ".join(filter(None, (author.get("given"), author.get("family"))))
            or author.get("display_name", "")
            for author in authors
        ]
        published = metadata.get("published", {}).get("date-parts", [[]])
        year = published[0][0] if published and published[0] else ""
        journal = metadata.get("container-title", "")
        if isinstance(journal, list):
            journal = journal[0] if journal else ""
        if not journal:
            journal = metadata.get("host_venue", {}).get("display_name", "")
        return {
            "doi": doi.lower(),
            "title": title or metadata.get("display_name", ""),
            "authors": [author for author in normalized_authors if author],
            "year": year or metadata.get("publication_year", ""),
            "journal": journal,
            "source": source,
        }

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
