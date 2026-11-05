"""Verificador de DOI en Crossref, OpenAlex y ORCID."""
from __future__ import annotations

from typing import Any, Dict


def verify_doi(doi: str, crossref, openalex, orcid) -> Dict[str, Any]:
    """Devuelve metadata verificada o razón de rechazo."""
    meta: Dict[str, Any] | None = None
    source: str | None = None

    cr = crossref.fetch(doi)
    if cr:
        meta, source = cr, "crossref"
    else:
        oa = openalex.fetch(doi)
        if oa:
            meta, source = oa, "openalex"
        else:
            orc = orcid.search_by_doi(doi)
            if orc:
                meta, source = orc, "orcid"

    if not meta:
        return {
            "ok": False,
            "reason": "DOI no verificado en Crossref/OpenAlex/ORCID",
        }

    return {"ok": True, "source": source, "metadata": meta}
