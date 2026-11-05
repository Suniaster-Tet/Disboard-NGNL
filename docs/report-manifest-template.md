# Plantilla de manifiesto de informe (`report-manifest.json`)

Estructura que `tools/document_generator.py` espera para compilar preprints,
informes y slides de forma determinista.

## Esquema

```json
{
  "title": "DisboardReportManifest",
  "type": "object",
  "required": ["edge_id", "title", "author_sovereign", "version", "sources", "outputs"],
  "properties": {
    "edge_id": {"type": "string", "example": "edge-condensado-bose-einstein"},
    "title": {"type": "string", "example": "Modelado teórico de condensados de Bose-Einstein"},
    "author_sovereign": {"type": "string", "default": "Tet"},
    "version": {"type": "string", "default": "1.0.0"},
    "sources": {"type": "array"},
    "outputs": {"type": "array"}
  }
}
```

## Ejemplo de uso

```python
from tools.document_generator import DocumentGenerator

gen = DocumentGenerator()
gen.render_template("preprint.tex.j2", {
    "title": "Modelado teórico",
    "authors": [{"name": "Tet", "affiliation": "Elkia"}],
    "date": "2026-01-15",
    "sections": [
        {"title": "Introducción", "content": "...", "subsections": []},
    ],
    "bibliography": "referencias.bib",
}, "edges/edge-condensado/out/preprint.tex")
```
