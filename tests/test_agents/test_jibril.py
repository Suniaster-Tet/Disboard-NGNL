"""Pruebas de Jibril."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.jibril.agent import JibrilScientific
from agents.jibril.doi_verifier import verify_doi


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------
class FakeCrossref:
    def __init__(self, result=None):
        self.result = result

    def fetch(self, doi):
        if self.result == "raise":
            raise RuntimeError("crossref down")
        return self.result


class FakeOpenAlex:
    def __init__(self, result=None):
        self.result = result

    def fetch(self, doi):
        return self.result


class FakeOrcid:
    def __init__(self, result=None):
        self.result = result

    def search_by_doi(self, doi):
        return self.result


# ---------------------------------------------------------------------------
# verify_doi
# ---------------------------------------------------------------------------
def test_verify_doi_crossref():
    res = verify_doi(
        "10.1/x",
        FakeCrossref({"title": "T", "doi": "10.1/x"}),
        FakeOpenAlex(None),
        FakeOrcid(None),
    )
    assert res["ok"] is True
    assert res["source"] == "crossref"


def test_verify_doi_openalex_fallback():
    res = verify_doi(
        "10.1/x",
        FakeCrossref(None),
        FakeOpenAlex({"title": "T", "doi": "10.1/x"}),
        FakeOrcid(None),
    )
    assert res["ok"] is True
    assert res["source"] == "openalex"


def test_verify_doi_orcid_fallback():
    res = verify_doi(
        "10.1/x",
        FakeCrossref(None),
        FakeOpenAlex(None),
        FakeOrcid({"title": "T", "doi": "10.1/x"}),
    )
    assert res["ok"] is True
    assert res["source"] == "orcid"


def test_verify_doi_inexistent():
    res = verify_doi(
        "10.1/x",
        FakeCrossref(None),
        FakeOpenAlex(None),
        FakeOrcid(None),
    )
    assert res["ok"] is False
    assert "no verificado" in res["reason"].lower() or "not verified" in res["reason"].lower()


# ---------------------------------------------------------------------------
# JibrilScientific
# ---------------------------------------------------------------------------
def test_fetch_many_separates_ok_and_rejected():
    j = JibrilScientific(edge_id="edge-test")
    # Reemplazamos los clientes por fakes controlados
    j.crossref = FakeCrossref({"title": "T1", "doi": "10.1/ok"})
    j.openalex = FakeOpenAlex(None)
    j.orcid = FakeOrcid(None)

    result = j.fetch_many(["10.1/ok"])
    assert len(result["ok"]) == 1
    assert result["rejected"] == []


def test_fetch_many_all_rejected():
    j = JibrilScientific(edge_id="edge-test")
    j.crossref = FakeCrossref(None)
    j.openalex = FakeOpenAlex(None)
    j.orcid = FakeOrcid(None)

    result = j.fetch_many(["10.1/missing"])
    assert result["ok"] == []
    assert len(result["rejected"]) == 1


def test_generate_bibtex_entry():
    j = JibrilScientific(edge_id="edge-test")
    bib = j.generate_bibtex_entry({
        "doi": "10.1/x",
        "title": "T",
        "authors": ["A", "B"],
        "year": 2026,
        "journal": "J",
    })
    assert "@article{" in bib
    assert "doi = {10.1/x}" in bib
    assert "A and B" in bib


def test_export_bibtex_multiple():
    j = JibrilScientific(edge_id="edge-test")
    bib = j.export_bibtex([
        {"doi": "10.1/a", "title": "A", "authors": ["A"], "year": 2026, "journal": "J"},
        {"doi": "10.1/b", "title": "B", "authors": ["B"], "year": 2026, "journal": "J"},
    ])
    assert bib.count("@article{") == 2


def test_enrich_reservoir_writes_jsonl(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    j = JibrilScientific(edge_id="edge-test")
    proposals = [{"doi": "10.1/x", "title": "T"}]
    path = j.enrich_reservoir(proposals)
    assert path is not None
    assert path.exists()
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["doi"] == "10.1/x"


def test_enrich_reservoir_without_edge_returns_none():
    j = JibrilScientific(edge_id=None)
    assert j.enrich_reservoir([{"doi": "10.1/x"}]) is None
