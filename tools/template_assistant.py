"""Generación de contexto para plantillas usando evidencia aprobada por Tet."""
from __future__ import annotations

import json
import re
from datetime import date
from typing import Any

from privacy.filters import filter_sensitive_data
from suniaster.inference import ModelUnavailable, invoke_agent

TEMPLATE_AGENTS = {
    "preprint.tex.j2": "stephanie",
    "report.md.j2": "stephanie",
    "slides.md.j2": "stephanie",
    "email.md.j2": "fiel",
}
DOI_PATTERN = re.compile(r"10\.\d{4,9}/[A-Za-z0-9._;()/:+-]+", re.IGNORECASE)


class TemplateAssistant:
    """Produce un contexto de plantilla sin inventar o importar referencias."""

    def generate_context(
        self,
        template_name: str,
        title: str,
        instructions: str,
        bibliography: list[dict[str, Any]],
        theories: list[str],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if template_name not in TEMPLATE_AGENTS:
            raise ValueError(f"Plantilla no habilitada: {template_name}")
        references = [
            {
                "doi": item.get("doi", ""),
                "title": item.get("title", ""),
                "authors": item.get("authors", []),
                "year": item.get("year", ""),
                "journal": item.get("journal", ""),
            }
            for item in bibliography
        ]
        allowed_dois = {item["doi"].lower() for item in references if item["doi"]}
        agent = TEMPLATE_AGENTS[template_name]
        prompt = self._prompt(template_name, title, instructions, references, theories)
        try:
            result = invoke_agent(agent, prompt)
        except ModelUnavailable as error:
            return self._fallback(template_name, title, instructions, references), {
                "mode": "template_only",
                "reason": str(error),
                "agent": agent,
                "provider": None,
                "model": None,
            }
        if result is None:
            return self._fallback(template_name, title, instructions, references), {
                "mode": "template_only",
                "reason": "llm_disabled_or_unavailable",
                "agent": agent,
                "provider": None,
                "model": None,
            }

        try:
            generated = json.loads(self._strip_code_fence(result["text"]))
            context = self._validate_context(template_name, generated, allowed_dois)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            return self._fallback(template_name, title, instructions, references), {
                "mode": "template_only",
                "reason": f"invalid_model_output:{type(error).__name__}",
                "agent": agent,
                "provider": result.get("provider"),
                "model": result.get("model"),
            }

        context.update(
            title=filter_sensitive_data(title),
            date=date.today().isoformat(),
            authors=["Tet"],
            author="Tet",
            bibliography="references",
            references=references,
        )
        if template_name == "preprint.tex.j2":
            context["authors"] = [{"name": "Tet", "affiliation": ""}]
        provenance = {
            "mode": "model",
            "agent": agent,
            "provider": result.get("provider"),
            "model": result.get("model"),
            "references": sorted(allowed_dois),
            "theories": list(theories),
        }
        return self._filter_context(context), provenance

    @staticmethod
    def _prompt(
        template_name: str,
        title: str,
        instructions: str,
        references: list[dict[str, Any]],
        theories: list[str],
    ) -> str:
        fields = {
            "preprint.tex.j2": "abstract:string, sections:[{title:string,content:string,subsections:[{title,content}]}]",
            "report.md.j2": "summary:string, sections:[{title:string,content:string,table_headers?:[string],table_data?:[[string]]}]",
            "slides.md.j2": "subtitle:string, slides:[{title:string,content?:string,bullets?:[string]}]",
            "email.md.j2": "recipient_role:string, subject:string, body:string, signature:string",
        }[template_name]
        return (
            "Redacta el contenido de una plantilla personal. Devuelve únicamente JSON válido "
            f"con estos campos: {fields}. Mantén la estructura y el enfoque indicado por Tet. "
            "Usa solo las teorías y referencias proporcionadas; no inventes autores, DOI, datos, "
            "resultados ni citas. Asocia afirmaciones científicas con DOI aprobado en el texto. "
            "Si falta evidencia, decláralo como límite o pregunta abierta.\n"
            f"PLANTILLA: {template_name}\nTÍTULO: {title}\n"
            f"INSTRUCCIONES DE TET: {instructions}\n"
            f"TEORÍAS DEFINIDAS POR TET: {json.dumps(theories, ensure_ascii=False)}\n"
            f"REFERENCIAS APROBADAS POR TET: {json.dumps(references, ensure_ascii=False)}"
        )

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        value = text.strip()
        if value.startswith("```"):
            value = value.split("\n", 1)[-1].removesuffix("```").strip()
        return value

    def _validate_context(
        self, template_name: str, generated: Any, allowed_dois: set[str]
    ) -> dict[str, Any]:
        if not isinstance(generated, dict):
            raise TypeError("El contexto de plantilla debe ser un objeto JSON.")
        required = {
            "preprint.tex.j2": ("abstract", "sections"),
            "report.md.j2": ("summary", "sections"),
            "slides.md.j2": ("subtitle", "slides"),
            "email.md.j2": ("recipient_role", "subject", "body", "signature"),
        }[template_name]
        for field in required:
            if field not in generated:
                raise ValueError(f"Falta el campo {field}.")
        serialized = json.dumps(generated, ensure_ascii=False)
        cited_dois = {doi.lower().rstrip(".,;)") for doi in DOI_PATTERN.findall(serialized)}
        if not cited_dois.issubset(allowed_dois):
            raise ValueError("El borrador contiene DOI que Tet no autorizó.")
        if len(serialized) > 250_000:
            raise ValueError("La respuesta supera el límite de tamaño.")
        return generated

    @staticmethod
    def _filter_context(value: Any) -> Any:
        if isinstance(value, str):
            return filter_sensitive_data(value)
        if isinstance(value, list):
            return [TemplateAssistant._filter_context(item) for item in value]
        if isinstance(value, dict):
            return {key: TemplateAssistant._filter_context(item) for key, item in value.items()}
        return value

    @staticmethod
    def _fallback(
        template_name: str,
        title: str,
        instructions: str,
        references: list[dict[str, Any]],
    ) -> dict[str, Any]:
        pending = "[Borrador pendiente: no hubo una respuesta válida de un modelo gratuito.]"
        if template_name == "preprint.tex.j2":
            context = {"abstract": pending, "sections": [{"title": "Contenido pendiente", "content": instructions, "subsections": []}]}
        elif template_name == "report.md.j2":
            context = {"summary": pending, "sections": [{"title": "Contenido pendiente", "content": instructions}]}
        elif template_name == "slides.md.j2":
            context = {"subtitle": "Borrador pendiente de revisión", "slides": [{"title": title, "bullets": [instructions, pending]}]}
        else:
            context = {
                "recipient_role": "Destinatario pendiente",
                "subject": title,
                "body": f"{instructions}\n\n{pending}",
                "signature": "Tet",
            }
        context.update(
            title=filter_sensitive_data(title),
            date=date.today().isoformat(),
            authors=["Tet"],
            author="Tet",
            bibliography="references",
            references=references,
        )
        if template_name == "preprint.tex.j2":
            context["authors"] = [{"name": "Tet", "affiliation": ""}]
        return TemplateAssistant._filter_context(context)