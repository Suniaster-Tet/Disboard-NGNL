"""Pruebas de datos, PDF, bibliografía y registro (contra agentes reales)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agents.base import SKILL_MAP, Agent
from agents.izuna.tensor_db import TensorDB
from agents.jibril.agent import JibrilScientific
from elkia.registry import ElkiaRegistry
from tools.pdf_extractor import PDFExtractor


class TensorDBTests(unittest.TestCase):
    def test_insert_and_query(self):
        with tempfile.TemporaryDirectory() as td:
            db = TensorDB(path=Path(td) / "tensor.jsonl")
            db.insert({"a": 1})
            self.assertEqual(len(db.query()), 1)


class PdfExtractorTests(unittest.TestCase):
    def test_extract_dois(self):
        try:
            from reportlab.pdfgen import canvas
        except ImportError:
            self.skipTest("reportlab no instalado")
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "p.pdf"
            pdf = canvas.Canvas(str(src))
            pdf.drawString(72, 720, "DOI: 10.1234/seed.1. Ref: 10.5678/ref.2")
            pdf.save()
            res = PDFExtractor().extract_text_and_dois(src)
            self.assertIn("10.1234/seed.1", res["dois"])


class JibrilTests(unittest.TestCase):
    def test_bibtex(self):
        j = JibrilScientific(edge_id="edge-test")
        bib = j.generate_bibtex_entry({
            "doi": "10.1/x", "title": "T", "authors": ["A"],
            "year": 2026, "journal": "J"})
        self.assertIn("@article{", bib)
        self.assertIn("doi = {10.1/x}", bib)


class RegistryTests(unittest.TestCase):
    def test_empty(self):
        with tempfile.TemporaryDirectory() as td:
            reg = ElkiaRegistry(ruta=Path(td) / "elkia.json")
            self.assertEqual(reg.listar(), [])


class SkillTests(unittest.TestCase):
    def test_every_agent_has_skill(self):
        for agent in SKILL_MAP:
            with self.subTest(agent=agent):
                contenido = Agent.load_skill(agent)
                self.assertIn("name:", contenido)


if __name__ == "__main__":
    unittest.main()
