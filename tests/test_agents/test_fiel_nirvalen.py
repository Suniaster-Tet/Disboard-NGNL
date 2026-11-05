"""Pruebas de Fiel Nirvalen."""
from agents.fiel_nirvalen.agent import FielNirvalen
from agents.fiel_nirvalen.privacy_filter import filter_sensitive_data


def test_email_filter():
    assert "[EMAIL_PROTECTED]" in filter_sensitive_data("a@b.com")


def test_phone_filter():
    assert "[PHONE_PROTECTED]" in filter_sensitive_data("555-123-4567")


def test_executive_report():
    fiel = FielNirvalen(edge_id="edge-test")
    rep = fiel.compile_executive_report("edge-test", ["Hito A"])
    assert "Hito A" in rep
