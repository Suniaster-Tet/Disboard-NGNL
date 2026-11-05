"""Cliente OpenAlex."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx

BASE = "https://api.openalex.org/works/https://doi.org/"


class OpenAlexClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENALEX_API_KEY", "")
        self.rate_limit_rps = 30 if self.api_key else 10

    def fetch(self, doi: str) -> Optional[Dict[str, Any]]:
        params = {"api_key": self.api_key} if self.api_key else {}
        try:
            r = httpx.get(BASE + doi, params=params, timeout=15)
        except httpx.HTTPError:
            return None
        if r.status_code != 200:
            return None
        return r.json()
