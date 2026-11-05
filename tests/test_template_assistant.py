"""Pruebas del redactor modular de plantillas científicas y administrativas."""
from __future__ import annotations

import json

from tools.template_assistant import TemplateAssistant


REFERENCE = {
    "doi": "10.1234/approved",
    "title": "Método reproducible",
    "authors": ["A. Autor"],
    "year": 2026,
    "journal": "Journal of Tests",
}


def test_template_context_uses_only_approved_scientific_evidence(monkeypatch):
    generated = {
        "summary": "El método se describió en 10.1234/approved.",
        "sections": [{"title": "Métodos", "content": "Aplicar el protocolo aprobado."}],
    }
    captured = {}

    def fake_invoke(agent, prompt):
        captured["agent"] = agent
        captured["prompt"] = prompt
        return {"text": json.dumps(generated), "provider": "groq", "model": "free-model"}

    monkeypatch.setattr("tools.template_assistant.invoke_agent", fake_invoke)
    context, provenance = TemplateAssistant().generate_context(
        "report.md.j2",
        "Informe reproducible",
        "Explicar métodos y límites.",
        [REFERENCE],
        ["Teoría de grafos definida por Tet"],
    )

    assert captured["agent"] == "stephanie"
    assert "Teoría de grafos definida por Tet" in captured["prompt"]
    assert "10.1234/approved" in context["summary"]
    assert provenance["provider"] == "groq"
    assert context["title"] == "Informe reproducible"


def test_unapproved_doi_forces_visible_template_fallback(monkeypatch):
    monkeypatch.setattr(
        "tools.template_assistant.invoke_agent",
        lambda agent, prompt: {
            "text": json.dumps({
                "abstract": "Afirmación sin sustento 10.9999/inventado",
                "sections": [{"title": "Resultados", "content": "Texto"}],
            }),
            "provider": "groq",
            "model": "free-model",
        },
    )

    context, provenance = TemplateAssistant().generate_context(
        "preprint.tex.j2", "Preprint", "Instrucciones", [REFERENCE], []
    )

    assert provenance["mode"] == "template_only"
    assert "Borrador pendiente" in context["abstract"]
    assert "10.9999/inventado" not in context["abstract"]


def test_email_template_is_draft_only_when_model_is_unavailable(monkeypatch):
    monkeypatch.setattr("tools.template_assistant.invoke_agent", lambda agent, prompt: None)
    context, provenance = TemplateAssistant().generate_context(
        "email.md.j2", "Solicitud", "Pedir comentarios sobre el informe.", [REFERENCE], []
    )

    assert provenance["agent"] == "fiel"
    assert provenance["mode"] == "template_only"
    assert "Borrador pendiente" in context["body"]
    assert "10.1234/approved" in context["references"][0]["doi"]


def test_all_base_templates_render_without_model(monkeypatch, tmp_path):
    from tools.document_generator import DocumentGenerator

    monkeypatch.setattr("tools.template_assistant.invoke_agent", lambda agent, prompt: None)
    assistant = TemplateAssistant()
    generator = DocumentGenerator()
    templates = {
        "preprint.tex.j2": "preprint.tex",
        "report.md.j2": "report.md",
        "slides.md.j2": "slides.md",
        "email.md.j2": "email.md",
    }
    for template_name, output_name in templates.items():
        context, _ = assistant.generate_context(
            template_name, "Borrador de prueba", "Contenido definido por Tet", [], []
        )
        result = generator.render_template(template_name, context, tmp_path / output_name)
        assert result["status"] == "success", result
        assert (tmp_path / output_name).is_file()
