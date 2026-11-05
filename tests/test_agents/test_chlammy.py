"""Pruebas de Chlammy."""
from agents.chlammy.agent import ChlammyAuditor


def test_alineacion_ok():
    ch = ChlammyAuditor(edge_id="edge-test")
    res = ch.verify_contract_alignment(
        {"objetivos": ["O1"]}, [{"id": "E1"}])
    assert res["aligned"] is True


def test_alineacion_falla_sin_entregables():
    ch = ChlammyAuditor(edge_id="edge-test")
    res = ch.verify_contract_alignment({"objetivos": ["O1"]}, [])
    assert res["aligned"] is False


def test_review_code_division_cero():
    ch = ChlammyAuditor(edge_id="edge-test")
    res = ch.review_code_and_math("return x / y", "division")
    assert res["status"] == "NEEDS_REVISION"
