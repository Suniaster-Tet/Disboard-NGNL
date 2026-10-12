import contextlib
import io
import json
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from disboard_console import DisboardConsole
from kuhaku_pipeline import KuhakuPipeline
from nirvalen_assistant import NirvalenAssistant


class PublicDoiAuthorizationTests(unittest.TestCase):
    @patch.dict("os.environ", {"DISBOARD_ALLOW_PUBLIC_DOI_LOOKUP": ""})
    @patch("kuhaku_pipeline.requests.get")
    def test_doi_verification_does_not_call_public_apis_without_opt_in(self, get):
        valid, reason = KuhakuPipeline._validar_referencias_jibril(
            "Referencia con DOI 10.1234/example"
        )

        self.assertFalse(valid)
        self.assertIn("DISBOARD_ALLOW_PUBLIC_DOI_LOOKUP=1", reason)
        get.assert_not_called()


class EisenhowerMatrixTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.console = DisboardConsole.__new__(DisboardConsole)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _project(self, slug, due):
        project = self.root / slug
        project.mkdir()
        (project / "contract.md").write_text(
            f"- **Fecha objetivo:** {due}\n", encoding="utf-8"
        )

    def test_date_and_progress_assign_and_order_the_four_quadrants_locally(self):
        records = [
            {"id": "Q1", "slug": "edge-q1", "title": "Urgente e importante",
             "status": "EN_PROCESO", "progress": "40%", "next_action": "Avanzar Q1"},
            {"id": "Q2", "slug": "edge-q2", "title": "Importante",
             "status": "EN_PROCESO", "progress": "30%", "next_action": "Avanzar Q2"},
            {"id": "Q3", "slug": "edge-q3", "title": "Urgente",
             "status": "EN_PROCESO", "progress": "80%", "next_action": "Avanzar Q3"},
            {"id": "Q4", "slug": "edge-q4", "title": "No urgente",
             "status": "EN_PROCESO", "progress": "90%", "next_action": "Avanzar Q4"},
            {"id": "UNSET", "slug": "edge-unset", "title": "Sin fecha",
             "status": "EN_PROCESO", "progress": "20%", "next_action": "Agregar fecha"},
        ]
        self._project("edge-q1", "2026-10-10")
        self._project("edge-q2", "2026-11-01")
        self._project("edge-q3", "2026-10-07")
        self._project("edge-q4", "2026-11-20")
        (self.root / "edge-unset").mkdir()

        output = io.StringIO()
        with patch("disboard_console.ROOT_DIR", self.root):
            with contextlib.redirect_stdout(output):
                self.console._mostrar_matriz_eisenhower(
                    records, hoy=date(2026, 10, 5)
                )

        rendered = output.getvalue()
        self.assertIn("Q1 · URGENTE E IMPORTANTE", rendered)
        self.assertIn("Q2 · IMPORTANTE, NO URGENTE", rendered)
        self.assertIn("Q3 · URGENTE, NO IMPORTANTE", rendered)
        self.assertIn("Q4 · NO URGENTE NI IMPORTANTE", rendered)
        self.assertIn("† dato faltante", rendered)
        self.assertLess(rendered.index("Q1 | Urgente e importante"),
                        rendered.index("Q2 | Importante"))
        self.assertIn("UNSET | Sin fecha", rendered)
        self.assertNotIn("SIN CLASIFICAR", rendered)

    def test_progress_parser_rejects_missing_and_out_of_range_values(self):
        self.assertEqual(self.console._avance_numerico("avance 49,5%"), 49.5)
        self.assertIsNone(self.console._avance_numerico("sin datos"))
        self.assertIsNone(self.console._avance_numerico("120%"))

    def test_contract_candidate_replaces_active_contract_only_after_tet_approval(self):
        project = self.root / "edge-contract"
        proposal_dir = project / "docs" / "propuestas_contractuales"
        proposal_dir.mkdir(parents=True)
        contract = project / "contract.md"
        contract.write_text("# Contrato anterior\n", encoding="utf-8")
        proposal = proposal_dir / "contract-candidate.md"
        proposal.write_text("# Contrato propuesto\n", encoding="utf-8")
        original_mode = contract.stat().st_mode & 0o777
        console = DisboardConsole.__new__(DisboardConsole)
        console.agent_gov = SimpleNamespace(
            registrar_en_bitacora_local=lambda *_: None
        )

        with patch("disboard_console.ROOT_DIR", self.root), \
                patch("builtins.input", return_value="1"), \
                patch.object(console, "_actualizar_registro_edge"):
            verdict = console.someter_a_veredicto_de_tet(
                "edge-contract",
                "docs/propuestas_contractuales/contract-candidate.md",
                "CONTRATO",
            )

        self.assertEqual(verdict, "APROBADO")
        self.assertEqual(contract.read_text(encoding="utf-8"), "# Contrato propuesto\n")
        if os.name == "posix":
            self.assertEqual(contract.stat().st_mode & 0o777, original_mode)

    def test_sora_status_suggestion_changes_registry_only_after_tet_approval(self):
        console = DisboardConsole.__new__(DisboardConsole)
        suggestion = {
            "avance": 35,
            "siguiente_accion": "Validar el análisis con Tet.",
            "archivos": ["src/solicitud.py"],
        }
        console.pipeline = SimpleNamespace(
            sugerencias_estado={"edge-test": suggestion}
        )
        update = []
        console._actualizar_registro_edge = lambda slug, **values: update.append(
            (slug, values)
        )

        console._aplicar_sugerencia_estado(
            "edge-test", "docs/propuestas_contractuales/contract-candidate.md"
        )
        self.assertEqual(console.pipeline.sugerencias_estado["edge-test"], suggestion)
        self.assertEqual(update, [])

        with patch("builtins.input", return_value="n"), \
                contextlib.redirect_stdout(io.StringIO()):
            console._aplicar_sugerencia_estado("edge-test", "src/solicitud.py")
        self.assertEqual(update, [])

        console.pipeline.sugerencias_estado["edge-test"] = suggestion
        with patch("builtins.input", return_value="s"), \
                contextlib.redirect_stdout(io.StringIO()):
            console._aplicar_sugerencia_estado("edge-test", "src/solicitud.py")
        self.assertEqual(
            update,
            [(
                "edge-test",
                {
                    "progress": "35%",
                    "next_action": "Validar el análisis con Tet.",
                    "milestone": "Tet aprobó una propuesta de avance de Sora",
                },
            )],
        )

    def test_agenda_matrix_reads_general_agenda_and_shows_missing_metadata(self):
        agenda_path = self.root / "AGENDAS_Y_CURSOS.md"
        agenda_path.write_text(
            "# Agenda\n"
            "- [Pendiente] Entregar propuesta | Fecha límite: 2026-10-08 | Avance: 20%\n"
            "- [En curso] Leer material | Fecha límite: SIN_FECHA | Avance: 60%\n",
            encoding="utf-8",
        )
        self.console.audit_supp = NirvalenAssistant(
            self.root, self.root / "Elkia.md", agenda_path
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.console._mostrar_matriz_agenda(hoy=date(2026, 10, 5))
        rendered = output.getvalue()

        self.assertIn("Q1 · URGENTE E IMPORTANTE", rendered)
        self.assertIn("Entregar propuesta", rendered)
        self.assertIn("Q4 · NO URGENTE NI IMPORTANTE", rendered)
        self.assertIn("Leer material", rendered)

    def test_free_request_router_dispatches_to_the_selected_project_agent(self):
        route = {
            "action": "project",
            "project_id": "GRAPHOS",
            "specialist": "Shiro",
        }
        console = DisboardConsole.__new__(DisboardConsole)
        console.agent_gov = SimpleNamespace(
            consultar_ia=lambda *args, **kwargs: (
                json.dumps(route),
                "local/router",
            ),
            _es_error_de_inferencia=lambda response: response.startswith("[Error"),
        )
        console._procesar_peticion_tet = lambda slug, request: ("stored", slug, request)
        received = []
        console._ejecutar_peticion_proyecto = (
            lambda *args: received.append(args)
        )
        records = [
            {"id": "GRAPHOS", "slug": "edge-graphos", "title": "Redes"},
        ]

        with patch("builtins.input", return_value="n"):
            console._procesar_peticion_libre(
                "GRAPHOS: genera el análisis", records
            )

        self.assertEqual(
            received,
            [("edge-graphos", "GRAPHOS: genera el análisis", True, "Shiro")],
        )

    def test_email_request_bypasses_ai_router_before_local_anonymization(self):
        console = DisboardConsole.__new__(DisboardConsole)

        def unexpected_router(*_args, **_kwargs):
            self.fail("El texto original del correo no debe llegar al router IA.")

        console.agent_gov = SimpleNamespace(consultar_ia=unexpected_router)
        received = []
        console.audit_supp = SimpleNamespace(
            fiel_redactar_correo=lambda **kwargs: received.append(kwargs)
        )

        with patch("builtins.input", return_value="n"):
            console._procesar_peticion_libre(
                "Responde este correo: Ana Perez <ana@example.org>", []
            )

        self.assertEqual(
            received,
            [{
                "directriz": "Responde este correo: Ana Perez <ana@example.org>",
                "solo_local": True,
            }],
        )

    def test_agenda_item_update_requires_exact_unique_match(self):
        agenda_path = self.root / "AGENDAS_Y_CURSOS.md"
        agenda_path.write_text(
            "# Agenda\n- [Pendiente] Reunión | Fecha límite: 2026-10-20 | Avance: 0%\n",
            encoding="utf-8",
        )
        assistant = NirvalenAssistant(
            self.root, self.root / "Elkia.md", agenda_path
        )

        assistant.actualizar_evento_agenda(
            "Reunión", status="En curso", avance=40
        )

        updated = agenda_path.read_text(encoding="utf-8")
        self.assertIn("[En curso] Reunión", updated)
        self.assertIn("Fecha límite: 2026-10-20", updated)
        self.assertIn("Avance: 40%", updated)
        with self.assertRaisesRegex(LookupError, "exactamente"):
            assistant.actualizar_evento_agenda("Reunion", status="Completo")


if __name__ == "__main__":
    unittest.main()
