"""Pruebas de la consola HITL de Disboard-NGNL."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agents.fiel_nirvalen.agent import FielNirvalen
from console.main import build_parser, main as console_main


class CliTests(unittest.TestCase):
    def test_parser_has_commands(self):
        parser = build_parser()
        for cmd in ("start", "check-models", "status", "dashboard",
                    "continue", "approve", "reject", "list-edges", "check-contract"):
            with self.subTest(cmd=cmd):
                ns = parser.parse_args([cmd, "edge-x"] if cmd in {"continue", "approve", "reject", "check-contract"} else [cmd])
                self.assertTrue(callable(ns.func))

    def test_status_without_edges(self):
        with patch("console.main.ElkiaRegistry") as reg:
            reg.return_value.listar.return_value = []
            self.assertEqual(console_main(["status"]), 0)

    def test_check_models(self):
        with patch("console.main.SuniasterUpdater") as upd:
            upd.return_value.check_and_update.return_value = {
                "status": "ok", "details": {}, "agents_with_error": 0}
            self.assertEqual(console_main(["check-models"]), 0)


class FielNirvalenTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.fiel = FielNirvalen(edge_id="edge-test", root_dir=str(self.root))

    def tearDown(self):
        self.td.cleanup()

    def test_executive_report(self):
        report = self.fiel.compile_executive_report("edge-test", ["Hito 1", "Hito 2"])
        self.assertIn("edge-test", report)
        self.assertIn("Hito 1", report)

    def test_anonymized_email_filters_data(self):
        body = "Escribe a ana@example.org o llama al 555-123-4567."
        correo = self.fiel.draft_anonymized_email("revisor", "Asunto", body)
        self.assertIn("[EMAIL_PROTECTED]", correo)
        self.assertIn("[PHONE_PROTECTED]", correo)
        self.assertNotIn("ana@example.org", correo)


class EisenhowerMatrixTests(unittest.TestCase):
    @unittest.skip("Pendiente: método en ElkiaDashboard/console")
    def test_four_quadrants(self):
        pass


class AgendaTests(unittest.TestCase):
    @unittest.skip("Pendiente: método en console")
    def test_agenda(self):
        pass


class FreeRouterTests(unittest.TestCase):
    @unittest.skip("Pendiente: método en console")
    def test_router(self):
        pass


if __name__ == "__main__":
    unittest.main()
