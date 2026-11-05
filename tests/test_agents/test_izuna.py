"""Pruebas de Izuna."""
from agents.izuna.tensor_db import TensorDB


def test_tensor_db_insert_and_query(tmp_path):
    db = TensorDB(path=tmp_path / "t.jsonl")
    db.insert({"a": 1})
    assert len(db.query()) == 1
