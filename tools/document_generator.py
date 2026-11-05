"""Motor de plantillas para renderizar preprints (.tex), informes (.md) y slides (.md)."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Union

from jinja2 import Environment, FileSystemLoader, select_autoescape


class DocumentGenerator:
    def __init__(self, template_dir: Union[str, Path] = "templates"):
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(enabled_extensions=("html", "xml")),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

    def render_template(self, template_name: str, context: Dict[str, Any],
                        output_path: Union[str, Path]) -> Dict[str, Any]:
        """Renderiza una plantilla con los datos estructurados."""
        try:
            template = self.env.get_template(template_name)
        except Exception as e:
            return {"status": "error", "message": f"Plantilla no encontrada: {e}"}

        try:
            rendered = template.render(**context)
        except Exception as e:
            return {"status": "error", "message": f"Error al renderizar: {e}"}

        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(rendered, encoding="utf-8")
        return {
            "status": "success",
            "output_path": str(out_p),
            "size_bytes": len(rendered.encode("utf-8")),
        }
