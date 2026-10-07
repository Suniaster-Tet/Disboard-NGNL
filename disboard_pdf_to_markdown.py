#!/usr/bin/env python3
"""Convert extractable PDF text into page-preserving Markdown, without AI."""
import argparse
import hashlib
import re
import shutil
from pathlib import Path

from pypdf import PdfReader


DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _markdown_fence(text):
    longest = max((len(match.group()) for match in re.finditer(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def convert_pdf_to_markdown(root_dir, project_slug, pdf_path):
    """Save a PDF's extractable text by page and retain its original in the project."""
    if not re.fullmatch(r"edge-[A-Za-z0-9_-]+", project_slug):
        raise ValueError("Selecciona un proyecto edge válido.")
    root = Path(root_dir).expanduser().resolve()
    project = (root / project_slug).resolve()
    if project.parent != root or not (project / "contract.md").is_file():
        raise FileNotFoundError(f"No se encontró el contrato del proyecto {project_slug}.")

    source = Path(pdf_path).expanduser().resolve()
    if not source.is_file() or source.suffix.casefold() != ".pdf":
        raise ValueError("La ruta debe apuntar a un archivo PDF existente.")

    pdf_hash = _sha256(source)
    reader = PdfReader(str(source))
    if reader.is_encrypted:
        raise ValueError("El PDF está cifrado; proporciona una copia desbloqueada autorizada.")

    page_texts = []
    pages_without_text = []
    detected_dois = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        detected_dois.extend(
            match.group(0).rstrip(".,;)")
            for match in DOI_PATTERN.finditer(text)
        )
        if text.strip():
            page_texts.append((page_number, text, True))
        else:
            pages_without_text.append(page_number)
            page_texts.append((page_number, "", False))

    bibliography_dir = project / "docs" / "bibliografia"
    source_dir = bibliography_dir / "fuentes"
    source_dir.mkdir(parents=True, exist_ok=True)
    bibliography_dir.chmod(0o700)
    source_dir.chmod(0o700)
    stored_pdf = source_dir / f"{pdf_hash[:16]}.pdf"
    if source != stored_pdf.resolve():
        shutil.copy2(source, stored_pdf)
    stored_pdf.chmod(0o600)

    metadata = reader.metadata or {}
    title = str(metadata.title or source.stem).replace("\r", " ").replace("\n", " ").strip()
    title_fence = _markdown_fence(title)
    markdown_path = bibliography_dir / f"pdf-{pdf_hash[:16]}.md"
    unique_dois = list(dict.fromkeys(detected_dois))
    seed_doi = next(
        (
            match.group(0).rstrip(".,;)")
            for match in DOI_PATTERN.finditer(page_texts[0][1])
        ),
        "",
    ) if page_texts else ""
    lines = [
        "# Extracción textual del PDF",
        "",
        "> Transcripción del texto extraíble del PDF, separada por página. "
        "El PDF original se conserva como fuente canónica; esta conversión no preserva "
        "diseño, imágenes, gráficos, tablas como estructura ni texto incrustado como imagen.",
        "",
        "- **Título incrustado:**",
        "",
        title_fence,
        title,
        title_fence,
        "",
        f"- **Archivo fuente:** [`{stored_pdf.name}`](fuentes/{stored_pdf.name})",
        f"- **SHA-256:** `{pdf_hash}`",
        f"- **Páginas PDF:** {len(reader.pages)}",
        f"- **Páginas con texto extraído:** {len(page_texts) - len(pages_without_text)}",
        f"- **Páginas sin texto extraíble:** {', '.join(map(str, pages_without_text)) or 'Ninguna'}",
        "- **OCR:** no aplicado",
        f"- **DOI detectados:** {', '.join(f'`{doi}`' for doi in unique_dois) or 'Ninguno'}",
        "",
    ]
    for page_number, text, has_text in page_texts:
        fence = _markdown_fence(text)
        lines.extend([
            f"## Página {page_number}",
            "",
            fence,
            text.rstrip("\r\n") if has_text else "[Sin texto extraíble; página vacía o contenido visual/OCR requerido.]",
            fence,
            "",
        ])

    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    markdown_path.chmod(0o600)
    return {
        "markdown": markdown_path.relative_to(project).as_posix(),
        "pdf": stored_pdf.relative_to(project).as_posix(),
        "sha256": pdf_hash,
        "page_count": len(reader.pages),
        "pages_with_text": len(page_texts),
        "pages_without_text": pages_without_text,
        "dois": unique_dois,
        "seed_doi": seed_doi,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Extraer texto de PDF a Markdown por página. No usa IA ni OCR."
    )
    parser.add_argument("project", help="Slug del proyecto edge que recibirá los archivos.")
    parser.add_argument("pdf", help="Ruta a un PDF local.")
    parser.add_argument("--root", default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    try:
        result = convert_pdf_to_markdown(args.root, args.project, args.pdf)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"Markdown: {result['markdown']}")
    print(f"PDF original: {result['pdf']}")
    print(
        f"Páginas: {result['page_count']}; texto extraído: {result['pages_with_text']}; "
        f"sin texto extraíble: {result['pages_without_text']}"
    )


if __name__ == "__main__":
    main()
