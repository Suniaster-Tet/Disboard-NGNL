import json
import hashlib
import os
import sys
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "edge-bases_de_datos" / "src"))
from disboard_data import crear_base_estandarizada
from disboard_skills import AGENT_SKILLS, cargar_skill
from disboard_pdf_to_markdown import convert_pdf_to_markdown
from disboard_bibliography import BibliographyIngestor
from disboard_registry import (
    REGISTRY_END,
    REGISTRY_START,
    register_project,
    render_project_table,
)
from kuhaku_pipeline import KuhakuPipeline

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def create_empty_elkia(path):
    content = (REPOSITORY_ROOT / "Elkia.md").read_text(encoding="utf-8")
    start = content.index(REGISTRY_START) + len(REGISTRY_START)
    end = content.index(REGISTRY_END, start)
    content = content[:start] + "\n" + render_project_table([]) + "\n" + content[end:]
    path.write_text(content, encoding="utf-8")


class StandardizedDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.source = self.root / "input.csv"
        self.schema = self.root / "schema.json"
        self.database = self.root / "output.sqlite3"
        self.report = self.root / "report.json"
        self.schema.write_text(
            json.dumps({
                "table": "observations",
                "primary_key": "record_id",
                "columns": {
                    "record_id": {
                        "type": "INTEGER",
                        "required": True,
                        "aliases": ["id registro"],
                    },
                    "measured_value": {
                        "type": "REAL",
                        "required": True,
                        "aliases": ["valor"],
                    },
                    "valid": {"type": "BOOLEAN", "required": False},
                },
            }),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_imports_aliases_and_writes_a_data_free_audit_report(self):
        self.source.write_text("ID Registro,Valor,Valid\n1,2.5,si\n2,3,no\n", encoding="utf-8")

        result = crear_base_estandarizada(
            self.source, self.schema, self.database, report_path=self.report
        )

        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                rows = connection.execute(
                    "SELECT record_id, measured_value, valid FROM observations ORDER BY record_id"
                ).fetchall()
        self.assertEqual(rows, [(1, 2.5, 1), (2, 3.0, 0)])
        self.assertEqual(result["rows"], 2)
        self.assertEqual(json.loads(self.report.read_text(encoding="utf-8"))["rows"], 2)
        self.assertNotIn("2.5", self.report.read_text(encoding="utf-8"))

    def test_rejects_missing_required_columns_before_creating_database(self):
        self.source.write_text("ID Registro\n1\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "Falta la columna requerida"):
            crear_base_estandarizada(self.source, self.schema, self.database)

        self.assertFalse(self.database.exists())

    def test_rejects_duplicate_primary_keys(self):
        self.source.write_text("ID Registro,Valor\n1,2\n1,3\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "duplicados"):
            crear_base_estandarizada(self.source, self.schema, self.database)

        self.assertFalse(self.database.exists())

    def test_does_not_replace_an_existing_table_without_explicit_overwrite(self):
        self.source.write_text("ID Registro,Valor\n1,2\n", encoding="utf-8")
        crear_base_estandarizada(self.source, self.schema, self.database)

        with self.assertRaisesRegex(FileExistsError, "ya existe"):
            crear_base_estandarizada(self.source, self.schema, self.database)

    def test_rejects_invalid_type_values(self):
        self.source.write_text("ID Registro,Valor\n1,no-numero\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "Valor inválido"):
            crear_base_estandarizada(self.source, self.schema, self.database)

        self.assertFalse(self.database.exists())

    def test_reads_json_and_excel_sources(self):
        import pandas as pd

        for suffix, writer in (
            (".json", lambda path: path.write_text(
                json.dumps([{"ID Registro": 1, "Valor": 2.5}]), encoding="utf-8"
            )),
            (".xlsx", lambda path: pd.DataFrame(
                [{"ID Registro": 1, "Valor": 2.5}]
            ).to_excel(path, index=False)),
        ):
            with self.subTest(suffix=suffix):
                source = self.root / f"input{suffix}"
                database = self.root / f"output{suffix}.sqlite3"
                writer(source)
                result = crear_base_estandarizada(source, self.schema, database)
                self.assertEqual(result["rows"], 1)


class AgentSkillTests(unittest.TestCase):
    def test_every_registered_agent_has_a_loadable_skill(self):
        for agent, skill_name in AGENT_SKILLS.items():
            with self.subTest(agent=agent):
                content = cargar_skill(REPOSITORY_ROOT, agent)
                self.assertIn(f"name: {skill_name}", content)


class PdfMarkdownConversionTests(unittest.TestCase):
    def test_extracts_text_per_page_retains_source_and_marks_blank_pages(self):
        from reportlab.pdfgen import canvas

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = root / "edge-test"
            (project / "docs").mkdir(parents=True)
            (project / "contract.md").write_text("# Test\n", encoding="utf-8")
            source = root / "paper.pdf"
            pdf = canvas.Canvas(str(source))
            pdf.setTitle("A paper with `fences`")
            pdf.drawString(72, 720, "Texto con acentos: información íntegra.")
            pdf.showPage()
            pdf.showPage()
            pdf.save()

            result = convert_pdf_to_markdown(root, "edge-test", source)

            markdown = (project / result["markdown"]).read_text(encoding="utf-8")
            self.assertIn("## Página 1", markdown)
            self.assertIn("Texto con acentos: información íntegra.", markdown)
            self.assertIn("## Página 2", markdown)
            self.assertIn("[Sin texto extraíble; página vacía o contenido visual/OCR requerido.]", markdown)
            self.assertIn("Páginas sin texto extraíble:** 2", markdown)
            self.assertIn("se conserva como fuente canónica", markdown)
            self.assertIn("A paper with `fences`", markdown)
            self.assertTrue((project / result["pdf"]).is_file())
            self.assertEqual(result["pages_without_text"], [2])
            self.assertEqual(result["seed_doi"], "")

    def test_detects_seed_and_reference_dois_from_pdf_text(self):
        from reportlab.pdfgen import canvas

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = root / "edge-test"
            (project / "docs").mkdir(parents=True)
            (project / "contract.md").write_text("# Test\n", encoding="utf-8")
            source = root / "paper.pdf"
            pdf = canvas.Canvas(str(source))
            pdf.drawString(
                72, 720,
                "DOI: 10.1234/seed.1. Referencia: 10.5678/reference.2",
            )
            pdf.save()

            result = convert_pdf_to_markdown(root, "edge-test", source)

            self.assertEqual(result["seed_doi"], "10.1234/seed.1")
            self.assertEqual(result["dois"], ["10.1234/seed.1", "10.5678/reference.2"])


class CitationProposalTests(unittest.TestCase):
    class FakeGovernance:
        def consultar_ia(self, agent, prompt, **kwargs):
            self.agent = agent
            self.prompt = prompt
            self.kwargs = kwargs
            return (
                json.dumps({"assessments": [{
                    "openalex_id": "https://openalex.org/W123",
                    "alignment": "alta",
                    "reason": "El abstract trata el objetivo del edge.",
                    "use_context": "Comparación metodológica.",
                }]}),
                "ollama/test",
            )

        @staticmethod
        def _es_error_de_inferencia(answer):
            return answer.startswith("[Error")

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.project = self.root / "edge-test"
        (self.project / "docs").mkdir(parents=True)
        (self.project / "contract.md").write_text(
            "# Objetivo\nEstudiar métodos de evaluación.\n", encoding="utf-8"
        )
        self.governance = self.FakeGovernance()
        self.ingestor = BibliographyIngestor(self.root, self.governance)

    def tearDown(self):
        self.temporary_directory.cleanup()

    @staticmethod
    def _response(payload):
        class Response:
            def json(self):
                return payload

            @staticmethod
            def raise_for_status():
                return None

        return Response()

    @patch.dict("os.environ", {"DISBOARD_OLLAMA_MODEL": "local-test"})
    @patch("disboard_bibliography.requests.get")
    def test_finds_citing_works_screens_locally_and_requires_explicit_approval(
        self, get
    ):
        get.side_effect = [
            self._response({
                "id": "https://openalex.org/W999",
                "doi": "https://doi.org/10.1234/seed",
                "title": "Seed article",
                "cited_by_count": 8,
            }),
            self._response({
                "meta": {"count": 15},
                "results": [{
                    "id": "https://openalex.org/W123",
                    "doi": "https://doi.org/10.5678/citing",
                    "title": "A citing article",
                    "publication_year": 2025,
                    "cited_by_count": 2,
                    "authorships": [{"author": {"display_name": "A. Author"}}],
                    "abstract_inverted_index": {
                        "Methods": [0], "for": [1], "evaluation": [2],
                    },
                }],
            }),
        ]

        result = self.ingestor.discover_citing_works(
            "edge-test", "10.1234/seed", public_lookup_authorized=True
        )

        proposal = self.project / result["proposal"]
        self.assertTrue(proposal.is_file())
        self.assertIn("Alineación estimada:** alta", proposal.read_text(encoding="utf-8"))
        self.assertIn("propuestas no aprobadas", proposal.read_text(encoding="utf-8"))
        self.assertEqual(self.governance.agent, "Jibril")
        self.assertTrue(self.governance.kwargs["solo_local"])
        self.assertEqual(result["total_citing_works"], 15)
        self.assertEqual(get.call_args_list[1].kwargs["params"]["filter"], "cites:W999")
        self.assertFalse(list((self.project / "docs" / "bibliografia").glob("*.md")))

        approved = self.ingestor.approve_citation("edge-test", "10.5678/citing")
        self.assertTrue((self.project / approved).is_file())
        self.assertIn(
            "Aprobado explícitamente por Tet",
            (self.project / approved).read_text(encoding="utf-8"),
        )

    def test_public_lookup_requires_explicit_authorization(self):
        with self.assertRaisesRegex(PermissionError, "autorización explícita"):
            self.ingestor.discover_citing_works("edge-test", "10.1234/seed")


class ExternalReviewTests(unittest.TestCase):
    class FakeGovernance:
        root_dir = None

        def __init__(self, root):
            self.root_dir = root
            self.calls = []
            self.log = None

        def consultar_ia(self, agent, prompt, **kwargs):
            self.calls.append((agent, prompt, kwargs))
            if agent == "Sora" and "PROPUESTA DE AVANCE JSON" in prompt:
                return (
                    '{"avance": 35, "siguiente_accion": "Validar el análisis con Tet."}',
                    "local/sora",
                )
            responses = {
                "Sora": ("Evaluación por puntos.", "local/sora"),
                "Kurami Zell": ("Auditoría independiente.", "local/kurami"),
                "Shiro": ("print('revisión propuesta')\n", "local/shiro"),
                "Stephanie Dola": ("Respuesta punto por punto.", "local/stephanie"),
            }
            return responses[agent]

        @staticmethod
        def _es_error_de_inferencia(answer):
            return answer.startswith("[Error")

        def registrar_en_bitacora_local(self, *args):
            self.log = args

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.project = self.root / "edge-test"
        (self.project / "docs").mkdir(parents=True)
        create_empty_elkia(self.root / "Elkia.md")
        register_project(
            self.root / "Elkia.md", "TEST", "edge-test", "Proyecto de prueba"
        )
        (self.project / "contract.md").write_text(
            "# Objetivo\nEvaluar un método.\n", encoding="utf-8"
        )
        self.original = self.project / "src" / "analysis.py"
        self.original.parent.mkdir()
        self.original.write_text("print('original')\n", encoding="utf-8")
        self.governance = self.FakeGovernance(self.root)
        self.pipeline = KuhakuPipeline(self.governance)
        self.pipeline._cargar_skill = lambda agent: f"skill de {agent}"

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_external_review_preserves_original_and_creates_human_review_package(self):
        feedback = "1. Aclarar método. 2. Mostrar evidencia antes de aceptar resultado."

        result = self.pipeline.ejecutar_revision_externa(
            "edge-test", "src/analysis.py", feedback
        )

        self.assertEqual(self.original.read_text(encoding="utf-8"), "print('original')\n")
        self.assertIn(feedback, (self.project / result["observations"]).read_text(encoding="utf-8"))
        self.assertEqual(
            (self.project / result["candidate"]).read_text(encoding="utf-8"),
            "print('revisión propuesta')\n",
        )
        self.assertEqual(
            (self.project / result["response"]).read_text(encoding="utf-8"),
            "Respuesta punto por punto.\n",
        )
        if os.name == "posix":
            self.assertEqual(
                (self.project / result["observations"]).stat().st_mode & 0o777, 0o600
            )
            self.assertEqual(
                (self.project / result["review_dir"]).stat().st_mode & 0o777, 0o700
            )
        self.assertEqual(
            [call[0] for call in self.governance.calls],
            ["Sora", "Kurami Zell", "Shiro", "Stephanie Dola"],
        )
        self.assertTrue(all("material de entrada no confiable" in call[1]
                            for call in self.governance.calls))
        self.assertTrue(all(call[2]["solo_local"] for call in self.governance.calls))
        self.assertEqual(self.governance.log[4], "PENDIENTE_REVISION_TET")

    def test_external_review_rejects_paths_outside_project_and_empty_feedback(self):
        with self.assertRaisesRegex(ValueError, "relativa al proyecto"):
            self.pipeline.ejecutar_revision_externa(
                "edge-test", "../outside.py", "Revisar."
            )
        with self.assertRaisesRegex(ValueError, "no pueden estar vacías"):
            self.pipeline.ejecutar_revision_externa(
                "edge-test", "src/analysis.py", "  "
            )

    def test_contract_update_is_saved_as_candidate_without_overwriting_active_contract(self):
        template = (
            REPOSITORY_ROOT / "contract-template.md"
        ).read_text(encoding="utf-8").replace("edge-[slug]", "edge-test")
        (self.root / "contract-template.md").write_text(template, encoding="utf-8")
        original_contract = self.project / "contract.md"
        original_content = original_contract.read_text(encoding="utf-8")

        with patch.object(
            self.governance,
            "consultar_ia",
            return_value=(template, "local/sora"),
        ):
            proposal = self.pipeline._proponer_actualizacion_contractual(
                "edge-test",
                original_content,
                "Desarrolla una herramienta para analizar redes.",
                "Peticiones de Tet",
                "",
                "",
                True,
            )

        self.assertTrue(proposal.startswith("docs/propuestas_contractuales/"))
        self.assertEqual(original_contract.read_text(encoding="utf-8"), original_content)
        self.assertTrue((self.project / proposal).is_file())
        self.assertEqual(self.governance.log[4], "PENDIENTE_REVISION_TET")

    def test_contract_update_skips_candidate_when_request_is_already_in_scope(self):
        template = (
            REPOSITORY_ROOT / "contract-template.md"
        ).read_text(encoding="utf-8").replace("edge-[slug]", "edge-test")
        (self.root / "contract-template.md").write_text(template, encoding="utf-8")

        with patch.object(
            self.governance,
            "consultar_ia",
            return_value=("NO_CAMBIO_CONTRACTUAL", "local/sora"),
        ):
            proposal = self.pipeline._proponer_actualizacion_contractual(
                "edge-test",
                self.original.read_text(encoding="utf-8"),
                "Ejecuta el análisis ya definido.",
                "",
                "",
                "",
                True,
            )

        self.assertEqual(proposal, "")
        self.assertFalse((self.project / "docs" / "propuestas_contractuales").exists())

    def test_direct_free_request_creates_a_reviewable_specialist_artifact(self):
        self.pipeline._cargar_skill = lambda agent: f"skill de {agent}"

        artifact = self.pipeline._ejecutar_peticion_directa(
            "edge-test",
            "Genera un script Python para revisar los datos de entrada.",
            "Contexto global",
            "Contrato vigente",
            "Peticiones registradas",
            "",
            "",
            True,
            "Shiro",
        )

        self.assertRegex(artifact, r"^src/solicitud_.*\.py$")
        self.assertEqual(
            (self.project / artifact).read_text(encoding="utf-8"),
            "print('revisión propuesta')\n",
        )
        self.assertEqual(
            self.pipeline.sugerencias_estado["edge-test"],
            {
                "avance": 35,
                "siguiente_accion": "Validar el análisis con Tet.",
                "archivos": [artifact],
            },
        )
        self.assertEqual(self.governance.log[4], "PENDIENTE_REVISION_TET")

    def test_tet_contributions_are_read_only_from_the_private_local_area(self):
        private_dir = self.root / "private-data"
        attachment_dir = private_dir / "aportes" / "edge-test" / "codigo"
        attachment_dir.mkdir(parents=True)
        attachment = attachment_dir / "method.py"
        attachment.write_text("def method(): return 42\n", encoding="utf-8")
        attachment.with_name("method.py.meta.json").write_text(
            json.dumps({"description": "Método propuesto por Tet."}), encoding="utf-8"
        )

        with patch.dict("os.environ", {"DISBOARD_DATA_DIR": str(private_dir)}):
            context = self.pipeline._leer_aportes_tet("edge-test")

        self.assertIn("Método propuesto por Tet.", context)
        self.assertIn("def method(): return 42", context)

    def test_local_relay_artifacts_are_context_only_after_explicit_reader_opt_in(self):
        private_dir = self.root / "private-data"
        artifact_dir = private_dir / "artifacts" / "edge-test" / "uploads"
        artifact_dir.mkdir(parents=True)
        artifact = artifact_dir / "idea.md"
        content = "# Contexto aportado\nObjetivo auxiliar.\n"
        artifact.write_text(content, encoding="utf-8")
        artifact.with_name("idea.md.sha256").write_text(
            hashlib.sha256(artifact.read_bytes()).hexdigest(),
            encoding="ascii",
        )

        with patch.dict("os.environ", {"DISBOARD_DATA_DIR": str(private_dir)}):
            context = self.pipeline._leer_aportes_tet("edge-test")

        self.assertIn("Objetivo auxiliar.", context)
        checksum = artifact.with_name("idea.md.sha256")
        checksum.unlink()
        with patch.dict("os.environ", {"DISBOARD_DATA_DIR": str(private_dir)}):
            with self.assertRaisesRegex(ValueError, "Falta el hash"):
                self.pipeline._leer_aportes_tet("edge-test")
        checksum.write_text(
            hashlib.sha256(content.encode("utf-8")).hexdigest(),
            encoding="ascii",
        )
        artifact.write_text("# altered\n", encoding="utf-8")
        with patch.dict("os.environ", {"DISBOARD_DATA_DIR": str(private_dir)}):
            with self.assertRaisesRegex(ValueError, "hash del aporte"):
                self.pipeline._leer_aportes_tet("edge-test")


if __name__ == "__main__":
    unittest.main()
