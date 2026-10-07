#!/usr/bin/env python3
"""Assemble reports from local project artifacts without invoking an LLM."""
import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf"}
CODE_EXTENSIONS = {".py", ".wl", ".nb", ".ipynb"}
MAX_TEXT_BYTES = 64_000
MAX_TABLE_ROWS = 30


def _latex(value):
    replacements = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
        "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
        "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in str(value))


def _safe_relative_file(project_dir, relative_path):
    source = (project_dir / relative_path).resolve()
    try:
        source.relative_to(project_dir.resolve())
    except ValueError as error:
        raise ValueError(f"La ruta sale del proyecto: {relative_path}") from error
    if not source.is_file():
        raise FileNotFoundError(f"No existe el artefacto: {relative_path}")
    return source


class DisboardReportBuilder:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir).resolve()

    def _project_dir(self, slug):
        if not re.fullmatch(r"edge-[A-Za-z0-9_-]+", slug):
            raise ValueError("El identificador debe ser una carpeta edge existente.")
        project_dir = (self.root_dir / slug).resolve()
        if project_dir.parent != self.root_dir or not (project_dir / "contract.md").is_file():
            raise FileNotFoundError(f"No se encontró un proyecto válido: {slug}")
        return project_dir

    @staticmethod
    def _read_manifest(project_dir, manifest_path):
        manifest_file = _safe_relative_file(project_dir, manifest_path)
        if manifest_file.suffix.lower() != ".json":
            raise ValueError("El manifiesto debe ser un archivo JSON.")
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        if not isinstance(manifest.get("sections"), list):
            raise ValueError("El manifiesto debe incluir una lista 'sections'.")
        return manifest

    @staticmethod
    def _artifact(project_dir, artifact):
        relative_path = artifact.get("path", "")
        source = _safe_relative_file(project_dir, relative_path)
        if source.stat().st_size > MAX_TEXT_BYTES and source.suffix.lower() not in IMAGE_EXTENSIONS:
            raise ValueError(f"El artefacto de texto excede {MAX_TEXT_BYTES} bytes: {relative_path}")
        return source, relative_path

    def build(self, slug, manifest_path="docs/report-manifest.json", output_format="tex", compile_pdf=False):
        project_dir = self._project_dir(slug)
        manifest = self._read_manifest(project_dir, manifest_path)
        if output_format not in {"tex", "md"}:
            raise ValueError("El formato debe ser 'tex' o 'md'.")
        if not manifest.get("title"):
            raise ValueError("El manifiesto debe incluir un título.")

        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        date_tag = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        title_slug = re.sub(r"[^a-z0-9]+", "-", manifest["title"].lower()).strip("-")[:48] or "informe"
        output_dir = project_dir / "docs" / "reportes"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{date_tag}-{title_slug}.{output_format}"
        source_hashes = {}

        def add_source(relative_path):
            source = _safe_relative_file(project_dir, relative_path)
            source_hashes[relative_path] = hashlib.sha256(source.read_bytes()).hexdigest()
            return source

        if output_format == "tex":
            content = self._render_latex(
                project_dir, output_dir, manifest, generated_at, source_hashes, add_source
            )
        else:
            content = self._render_markdown(
                project_dir, output_dir, manifest, generated_at, source_hashes, add_source
            )
        output_file.write_text(content, encoding="utf-8")
        result = {"source": output_file.relative_to(project_dir).as_posix(), "pdf": None}

        if compile_pdf:
            compiler = shutil.which("latexmk")
            if not compiler:
                raise RuntimeError("No se encontró latexmk; se generó el .tex, pero no el PDF.")
            completed = subprocess.run(
                [compiler, "-pdf", "-interaction=nonstopmode", "-halt-on-error",
                 f"-outdir={output_dir}", str(output_file)],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
            if completed.returncode:
                raise RuntimeError(completed.stderr[-3000:] or completed.stdout[-3000:])
            pdf_file = output_file.with_suffix(".pdf")
            result["pdf"] = pdf_file.relative_to(project_dir).as_posix()
        result["sources"] = [
            {"path": path, "sha256": digest} for path, digest in sorted(source_hashes.items())
        ]
        return result

    def _render_latex(self, project_dir, output_dir, manifest, generated_at, source_hashes, add_source):
        author = ", ".join(manifest.get("authors", [])) or "Disboard-NGNL"
        lines = [
            r"\documentclass[11pt]{article}",
            r"\usepackage[utf8]{inputenc}",
            r"\usepackage[T1]{fontenc}",
            r"\usepackage[margin=2.5cm]{geometry}",
            r"\usepackage{graphicx}",
            r"\usepackage{booktabs}",
            r"\usepackage{longtable}",
            r"\usepackage{hyperref}",
            r"\usepackage{verbatim}",
            r"\title{" + _latex(manifest["title"]) + "}",
            r"\author{" + _latex(author) + "}",
            r"\date{" + _latex(manifest.get("date", generated_at)) + "}",
            r"\begin{document}", r"\maketitle",
        ]
        if manifest.get("abstract"):
            lines.extend([r"\begin{abstract}", _latex(manifest["abstract"]), r"\end{abstract}"])

        for section in manifest["sections"]:
            lines.append(r"\section{" + _latex(section.get("title", "Resultados")) + "}")
            for paragraph in section.get("paragraphs", []):
                lines.extend([_latex(paragraph), ""])
            for artifact in section.get("artifacts", []):
                source, relative_path = self._artifact(project_dir, artifact)
                add_source(relative_path)
                caption = artifact.get("caption", source.name)
                suffix = source.suffix.lower()
                if suffix in IMAGE_EXTENSIONS:
                    image_path = Path(__import__("os").path.relpath(source, output_dir)).as_posix()
                    lines.extend([
                        r"\begin{figure}[htbp]\centering",
                        r"\includegraphics[width=0.92\linewidth]{\detokenize{" + image_path + "}}",
                        r"\caption{" + _latex(caption) + "}",
                        r"\end{figure}",
                    ])
                elif suffix == ".csv":
                    rows = list(csv.reader(source.open(encoding="utf-8-sig", newline="")))
                    if rows:
                        headers, data = rows[0], rows[1:MAX_TABLE_ROWS + 1]
                        column_spec = "l" * max(1, len(headers))
                        lines.extend([r"\begin{longtable}{" + column_spec + "}", r"\toprule"])
                        lines.append(" & ".join(_latex(cell) for cell in headers) + r" \\")
                        lines.append(r"\midrule")
                        lines.extend(" & ".join(_latex(cell) for cell in row[:len(headers)]) + r" \\" for row in data)
                        lines.extend([r"\bottomrule", r"\end{longtable}"])
                        if len(rows) - 1 > len(data):
                            lines.append(_latex(f"Tabla truncada a {len(data)} filas de {len(rows) - 1}."))
                        lines.append(r"\textit{" + _latex(caption) + "}")
                elif suffix in CODE_EXTENSIONS:
                    lines.append(r"\noindent\textbf{" + _latex(caption) + "}: " + _latex(relative_path))
                elif suffix in {".txt", ".json"}:
                    text = source.read_text(encoding="utf-8")[:MAX_TEXT_BYTES]
                    lines.extend([r"\paragraph{" + _latex(caption) + "}", r"\begin{verbatim}", text, r"\end{verbatim}"])
                else:
                    raise ValueError(f"Tipo de artefacto no admitido: {suffix}")

        lines.extend([r"\section*{Procedencia de datos}"])
        if not source_hashes:
            lines.append("No se adjuntaron artefactos externos.")
        else:
            lines.append(r"\begin{longtable}{p{0.48\linewidth}p{0.45\linewidth}}")
            lines.append(r"\toprule Archivo & SHA-256 \\\midrule")
            for path, digest in sorted(source_hashes.items()):
                lines.append(_latex(path) + " & " + r"\texttt{" + digest + r"} \\")
            lines.extend([r"\bottomrule", r"\end{longtable}"])
        lines.extend([r"\end{document}", ""])
        return "\n".join(lines)

    def _render_markdown(self, project_dir, output_dir, manifest, generated_at, source_hashes, add_source):
        lines = [f"# {manifest['title']}", "", f"**Tipo:** {manifest.get('document_type', 'Informe')}"]
        if manifest.get("authors"):
            lines.append(f"**Autores:** {', '.join(manifest['authors'])}")
        lines.extend([f"**Generado:** {manifest.get('date', generated_at)}", ""])
        if manifest.get("abstract"):
            lines.extend(["## Resumen", "", manifest["abstract"], ""])
        for section in manifest["sections"]:
            lines.extend([f"## {section.get('title', 'Resultados')}", ""])
            for paragraph in section.get("paragraphs", []):
                lines.extend([paragraph, ""])
            for artifact in section.get("artifacts", []):
                source, relative_path = self._artifact(project_dir, artifact)
                add_source(relative_path)
                report_relative = Path(__import__("os").path.relpath(source, output_dir)).as_posix()
                caption = artifact.get("caption", source.name)
                if source.suffix.lower() in IMAGE_EXTENSIONS:
                    lines.extend([f"![{caption}]({report_relative})", ""])
                elif source.suffix.lower() == ".csv":
                    rows = list(csv.reader(source.open(encoding="utf-8-sig", newline="")))
                    if rows:
                        lines.append("| " + " | ".join(rows[0]) + " |")
                        lines.append("| " + " | ".join("---" for _ in rows[0]) + " |")
                        lines.extend("| " + " | ".join(row) + " |" for row in rows[1:MAX_TABLE_ROWS + 1])
                        if len(rows) - 1 > MAX_TABLE_ROWS:
                            lines.append(f"\nTabla limitada a {MAX_TABLE_ROWS} filas; fuente completa: `{relative_path}`.")
                        lines.append("")
                elif source.suffix.lower() in CODE_EXTENSIONS:
                    lines.extend([f"Artefacto fuente: `{relative_path}`", ""])
                elif source.suffix.lower() in {".txt", ".json"}:
                    lines.extend([f"### {caption}", "", "```", source.read_text(encoding="utf-8")[:MAX_TEXT_BYTES], "```", ""])
                else:
                    raise ValueError(f"Tipo de artefacto no admitido: {source.suffix}")
        lines.extend(["## Procedencia de datos", ""])
        for path, digest in sorted(source_hashes.items()):
            lines.append(f"- `{path}` · SHA-256 `{digest}`")
        lines.append("")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Ensamblar informes con artefactos locales sin llamar modelos IA.")
    parser.add_argument("project", help="Slug de proyecto edge")
    parser.add_argument("--manifest", default="docs/report-manifest.json")
    parser.add_argument("--format", choices=("tex", "md"), default="tex")
    parser.add_argument("--pdf", action="store_true", help="Compilar el .tex generado usando latexmk")
    parser.add_argument("--root", default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    result = DisboardReportBuilder(args.root).build(
        args.project, args.manifest, args.format, args.pdf
    )
    print(f"Informe: {result['source']}")
    if result["pdf"]:
        print(f"PDF: {result['pdf']}")
    print(f"Artefactos con hash: {len(result['sources'])}")


if __name__ == "__main__":
    main()