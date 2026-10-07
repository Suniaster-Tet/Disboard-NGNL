import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nirvalen_assistant import NirvalenAssistant


class EmailPrivacyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.assistant = NirvalenAssistant(
            self.root,
            self.root / "Elkia.md",
            self.root / "AGENDAS_Y_CURSOS.md",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_sanitizer_redacts_addresses_contact_headers_and_urls(self):
        cleaned = self.assistant.limpiar_datos_personales(
            "De: Ana Perez <ana@example.org>\n"
            "Llamar al 555-123-4567 o revisar https://example.org/persona"
        )
        self.assertNotIn("Ana Perez", cleaned)
        self.assertNotIn("ana@example.org", cleaned)
        self.assertNotIn("555-123-4567", cleaned)
        self.assertNotIn("https://example.org/persona", cleaned)

    def test_only_confirmed_anonymized_email_reaches_the_ai_and_is_saved_privately(self):
        class FakeGovernance:
            def __init__(self):
                self.prompt = ""

            def consultar_ia(self, _agent, prompt, **_kwargs):
                self.prompt = prompt
                return "Estimado/a Destinatario general: podemos compartir la información.", "local"

            @staticmethod
            def _es_error_de_inferencia(answer):
                return answer.startswith("[Error")

        governance = FakeGovernance()
        self.assistant.governance = governance
        source = (
            "De: Ana Perez <ana@example.org>\n"
            "Necesito el informe. Teléfono: 555-123-4567."
        )
        with patch(
            "builtins.input",
            side_effect=[
                "Responderemos cuando el informe esté listo.",
                "Estado del informe",
                "Solicitud de información",
                "s",
                "s",
            ],
        ):
            self.assistant.fiel_redactar_correo(source, solo_local=True)

        self.assertNotIn("Ana Perez", governance.prompt)
        self.assertNotIn("ana@example.org", governance.prompt)
        self.assertNotIn("555-123-4567", governance.prompt)
        self.assertIn("Destinatario general", governance.prompt)
        guide = self.assistant.response_guide_path.read_text(encoding="utf-8")
        self.assertIn("Solicitud de información", guide)
        self.assertIn("podemos compartir la información", guide)
        self.assertNotIn("ana@example.org", guide)

    def test_uploaded_response_guide_is_sanitized_before_local_storage(self):
        source = self.root / "incoming-guide.md"
        source.write_text(
            "# Respuestas\n\n## Coordinación\nDe: Ana Perez <ana@example.org>\n"
            "Respuesta: agradecemos su mensaje.\n",
            encoding="utf-8",
        )
        with patch("builtins.input", return_value="sí"):
            imported = self.assistant.importar_guia_respuestas(source)

        self.assertTrue(imported)
        saved = self.assistant.response_guide_path.read_text(encoding="utf-8")
        self.assertNotIn("Ana Perez", saved)
        self.assertNotIn("ana@example.org", saved)
        self.assertIn("agradecemos su mensaje", saved)


if __name__ == "__main__":
    unittest.main()
