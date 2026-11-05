"""Auditoría de ejecución: inicialización, registro y cierre de reportes.

Complementa a `tools/reporter.py`. No instala dependencias ni detecta entorno
(eso vive en `tools/environment.py` y `scripts/healthcheck.py`).
"""
from __future__ import annotations

import inspect
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from tools.reporter import DataExporter, Reporter


def detect_main_process() -> str:
    """Devuelve el nombre del script o notebook que invocó la auditoría."""
    try:
        return Path(inspect.stack()[-1].filename).stem
    except Exception:  # pragma: no cover
        return "Unknown_Process"


def build_objective(process: str, task: Optional[str]) -> str:
    task = task or "Unspecified process"
    return f"Update of process '{process}' for the study of '{task}'."


def initialize_reports(
    filename: Optional[str] = None,
    process_name: Optional[str] = None,
    task: Optional[str] = None,
    objective: Optional[str] = None,
    environment: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Inicializa los reporteros Word y LaTeX y el contexto de auditoría."""
    process = process_name or detect_main_process()
    archive = filename or f"{process}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    archive = str(archive).strip().replace(" ", "_")
    objective = objective or build_objective(process, task)
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    environment = environment or {}

    word = Reporter(title=archive, use_latex=False)
    latex = Reporter(title=archive, use_latex=True)
    reporters = [word, latex]

    for rep in reporters:
        rep.add_section("Execution metadata")
        rep.add_paragraph(f"Date and time: {date}")
        rep.add_paragraph(f"Main process: {process}")
        rep.add_paragraph(f"Environment: {environment.get('environment', 'unknown')}")
        rep.add_paragraph(f"Python: {environment.get('python_version', 'unknown')}")
        rep.add_paragraph(f"Directory: {environment.get('cwd', 'unknown')}")

        rep.add_section("Process objective")
        rep.add_paragraph(objective)
        if task:
            rep.add_paragraph(f"Declared task: {task}")

        rep.add_section("Activity log")
        rep.add_section("Generated results")
        rep.add_section("Exported files and artifacts")

    return {
        "name": archive,
        "process": process,
        "task": task,
        "objective": objective,
        "created_at": date,
        "environment": environment,
        "word": word,
        "latex": latex,
        "reporters": reporters,
        "activities": [],
        "results": [],
        "artifacts": [],
        "exported_files": [],
    }


def register_activity(context: dict[str, Any], title: str, description: Optional[str] = None) -> None:
    context["activities"].append({
        "title": title,
        "description": description,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })


def register_result(context: dict[str, Any], name: str, value: Any) -> None:
    context["results"].append({"name": name, "value": value})


def register_artifact(context: dict[str, Any], name: str) -> None:
    context["artifacts"].append(str(name))


def _update_final_sections(context: dict[str, Any]) -> None:
    for rep in context["reporters"]:
        if context["activities"]:
            rep.add_subsection("Registered activities")
            for item in context["activities"]:
                text = f"[{item['timestamp']}] {item['title']}"
                if item["description"]:
                    text += f" | {item['description']}"
                rep.add_paragraph(text)

        if context["results"]:
            rep.add_subsection("Indicators and results")
            for item in context["results"]:
                rep.add_paragraph(f"{item['name']}: {item['value']}")

        if context["artifacts"]:
            rep.add_subsection("Registered artifacts")
            rep.add_list(context["artifacts"])


def finalize_reports(
    context: dict[str, Any],
    exporter: Optional[DataExporter] = None,
    export_csv: bool = True,
) -> dict[str, Any]:
    """Guarda Word/LaTeX/XLSX/CSV y devuelve las rutas generadas."""
    outputs: dict[str, Any] = {}
    base_name = context["name"]

    _update_final_sections(context)

    try:
        context["word"].save(base_name)
        docx_path = str(Path(f"{base_name}.docx").resolve())
        outputs["docx"] = docx_path
        context["exported_files"].append(docx_path)
    except Exception as e:  # pragma: no cover
        print(f"❌ Error DOCX: {e}")

    try:
        context["latex"].save(base_name)
        tex_path = str(Path(f"{base_name}.tex").resolve())
        outputs["tex"] = tex_path
        context["exported_files"].append(tex_path)
    except Exception as e:  # pragma: no cover
        print(f"❌ Error TEX: {e}")

    if exporter is not None and exporter.tables:
        try:
            excel_name = f"{base_name}.xlsx"
            exporter.save_excel(excel_name)
            excel_path = str(Path(excel_name).resolve())
            outputs["xlsx"] = excel_path
            context["exported_files"].append(excel_path)
        except Exception as e:  # pragma: no cover
            print(f"❌ Error XLSX: {e}")

        if export_csv:
            try:
                csv_paths = exporter.save_csvs("csv_exports")
                outputs["csv"] = csv_paths
                context["exported_files"].extend(csv_paths)
            except Exception as e:  # pragma: no cover
                print(f"❌ Error CSV: {e}")

    try:
        context["word"].cleanup()
        context["latex"].cleanup()
    except Exception:  # pragma: no cover
        pass

    return outputs
