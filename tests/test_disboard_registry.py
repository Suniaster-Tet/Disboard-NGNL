import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from elkia_architect import ElkiaArchitect
from kuhaku_pipeline import KuhakuPipeline
from disboard_registry import (
    agent_index_context,
    project_by_id,
    project_by_slug,
    project_records,
    REGISTRY_END,
    REGISTRY_START,
    read_master_index,
    render_project_table,
    register_project,
    update_project,
)
from disboard_graph import DisboardAgentGraph


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def create_empty_index(path: Path) -> None:
    content = (REPOSITORY_ROOT / "Elkia.md").read_text(encoding="utf-8")
    start = content.index(REGISTRY_START) + len(REGISTRY_START)
    end = content.index(REGISTRY_END, start)
    content = content[:start] + "\n" + render_project_table([]) + "\n" + content[end:]
    path.write_text(content, encoding="utf-8")


class ElkiaRegistryTests(unittest.TestCase):
    def test_active_registry_uses_current_schema_without_ngnl(self):
        content = read_master_index(REPOSITORY_ROOT / "Elkia.md")
        records = project_records(content)

        self.assertEqual(
            [record["id"] for record in records],
            ["DOIS", "DF", "PTE", "GRAPHOS"],
        )
        self.assertIsNone(project_by_id(content, "NGNL"))
        self.assertEqual(project_by_slug(content, "edge-bases_de_datos")["id"], "DF")
        self.assertEqual(project_by_id(content, "GRAPHOS")["slug"],
                         "edge-redes_cientificas_graphos")
        self.assertTrue(all(record["milestone"] for record in records))
        self.assertTrue(all(record["next_action"] for record in records))

    def test_agent_context_reads_global_rules_and_active_edges_without_tool_catalog(self):
        content = read_master_index(REPOSITORY_ROOT / "Elkia.md")
        context = agent_index_context(content)

        self.assertIn("Directrices de Arquitectura y Gobernanza", context)
        self.assertIn("Jibril", context)
        self.assertIn("edge-bases_de_datos", context)
        self.assertIn("skills/bibliografia-jibril/SKILL.md", context)
        self.assertIn("Informes y preprints desde manifiesto", context)
        self.assertIn("BLOQUEADO", context)
        self.assertNotIn("Google AI Studio", context)

    def test_master_index_fails_closed_when_global_capabilities_are_missing(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            malformed = Path(temporary_directory) / "Elkia.md"
            malformed.write_text(
                "<!-- REGISTRO_PROYECTOS_INICIO -->\n"
                "<!-- REGISTRO_PROYECTOS_FIN -->\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "está incompleto"):
                read_master_index(malformed)

    def test_registration_and_updates_keep_the_standardized_table_and_progress(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            master = Path(temporary_directory) / "Elkia.md"
            create_empty_index(master)
            register_project(master, "A-1", "edge-alpha", "Alpha")

            update_project(
                master,
                "edge-alpha",
                status="EN_PROCESO",
                milestone="Tet aprobó el primer informe",
                next_action="Continuar con el segundo hito",
            )
            content = read_master_index(master)
            record = project_by_id(content, "A-1")

            self.assertEqual(record["status"], "EN_PROCESO")
            self.assertEqual(record["progress"], "0%")
            self.assertEqual(record["milestone"], "Tet aprobó el primer informe")
            self.assertEqual(record["next_action"], "Continuar con el segundo hito")
            self.assertIn("| Último hito / movimiento |", content)
            with self.assertRaisesRegex(ValueError, "El ID ya existe"):
                register_project(master, "A-1", "edge-beta", "Beta")

    def test_project_lookup_matches_exact_ids_not_substrings(self):
        content = read_master_index(REPOSITORY_ROOT / "Elkia.md")
        self.assertIsNone(project_by_id(content, "DO"))
        self.assertEqual(project_by_id(content, "DOIS")["slug"], "edge-dataframe_dois_mineria")

    def test_langgraph_context_loads_elkia_before_a_registered_contract(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            master = root / "Elkia.md"
            create_empty_index(master)
            register_project(master, "TEST", "edge-test", "Test project")
            project = root / "edge-test"
            project.mkdir()
            (project / "contract.md").write_text("Contrato de prueba", encoding="utf-8")

            graph = DisboardAgentGraph(root)
            context = graph._contexto_proyecto("edge-test")

            self.assertLess(context.index("Elkia.md"), context.index("Contrato"))
            self.assertIn("Contrato de prueba", context)

    def test_langgraph_rejects_edges_missing_from_active_registry(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            create_empty_index(root / "Elkia.md")
            graph = DisboardAgentGraph(root)
            with self.assertRaisesRegex(ValueError, "no está registrado"):
                graph._contexto_proyecto("edge-unregistered")

    def test_new_contract_is_edge_specific_and_has_no_example_tasks(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            master = root / "Elkia.md"
            create_empty_index(master)
            template = REPOSITORY_ROOT / "contract-template.md"
            (root / "contract-template.md").write_text(
                template.read_text(encoding="utf-8"), encoding="utf-8"
            )
            architect = ElkiaArchitect(root, master)
            with patch(
                "builtins.input",
                side_effect=[
                    "alpha",
                    "ALPHA-1",
                    "Alpha Project",
                    "Crear herramientas para analizar redes y revisar literatura.",
                ],
            ):
                slug = architect.crear_nuevo_proyecto()

            contract = (root / slug / "contract.md").read_text(encoding="utf-8")
            deliverables = KuhakuPipeline(None)._entregables_del_contrato(contract)

            self.assertEqual(slug, "edge-alpha")
            self.assertIn("**ID del registro Elkia:** ALPHA-1", contract)
            self.assertIn("**Título específico:** Alpha Project", contract)
            self.assertNotIn("[slug]", contract)
            self.assertNotIn("P1", contract)
            self.assertNotIn("10%", contract)
            self.assertEqual(deliverables, [])
            self.assertIn("MÓDULO A", contract)
            self.assertIn("MÓDULO B", contract)
            self.assertIn("Crear herramientas para analizar redes y revisar literatura.", contract)
            self.assertEqual(
                project_by_id(read_master_index(master), "ALPHA-1")["slug"],
                "edge-alpha",
            )

    def test_contract_update_helpers_queue_requests_instead_of_mutating_contract(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            master = root / "Elkia.md"
            create_empty_index(master)
            project = root / "edge-alpha"
            (project / "docs").mkdir(parents=True)
            contract = project / "contract.md"
            contract.write_text("# Contrato aprobado\n", encoding="utf-8")
            architect = ElkiaArchitect(root, master)

            self.assertTrue(
                architect.actualizar_contexto_proyecto(
                    "edge-alpha", "objetivos", "Analizar datos."
                )
            )
            self.assertTrue(
                architect.agregar_a_seccion_contractual(
                    "edge-alpha", "entregable", "Reporte reproducible."
                )
            )

            self.assertEqual(
                contract.read_text(encoding="utf-8"), "# Contrato aprobado\n"
            )
            requests = (project / "docs" / "peticiones_tet.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("Analizar datos.", requests)
            self.assertIn("Reporte reproducible.", requests)


if __name__ == "__main__":
    unittest.main()
