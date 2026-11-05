"""Cliente Crossref (polite pool con mailto)."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx

BASE = "https://api.crossref.org/works/"


class CrossrefClient:
    def __init__(self, mailto: Optional[str] = None):
        self.mailto = mailto or os.getenv("CROSSREF_MAILTO", "")
        self.rate_limit_rps = 10 if self.mailto else 5

    def fetch(self, doi: str) -> Optional[Dict[str, Any]]:
        headers = (
            {"User-Agent": f"Disboard-NGNL/2.0 (mailto:{self.mailto})"}
            if self.mailto else {}
        )
        try:
            r = httpx.get(BASE + doi, headers=headers, timeout=15)
        except httpx.HTTPError:
            return None
        if r.status_code != 200:
            return None
        return r.json().get("message")
