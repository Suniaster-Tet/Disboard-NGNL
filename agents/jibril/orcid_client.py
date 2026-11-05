"""Cliente ORCID (público; token opcional para /read-limited)."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx

BASE = "https://pub.orcid.org/v3.0/"


class OrcidClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("ORCID_TOKEN", "")
        self.rate_limit_rps = 8
        self.rate_burst = 40

    def search_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            r = httpx.get(BASE + "search/?q=doi:" + doi, headers=headers, timeout=15)
        except httpx.HTTPError:
            return None
        if r.status_code != 200:
            return None
        return r.json()
