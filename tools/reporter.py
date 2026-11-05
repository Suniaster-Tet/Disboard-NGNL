"""Generación de reportes Word (.docx) y LaTeX (.tex).

Incluye:
- Paleta institucional (códigos Pantone).
- Estilos tipográficos.
- Utilidades de color y LaTeX.
- Clase `Reporter` con interfaz unificada para DOCX y LaTeX.
- `DataExporter` para exportar DataFrames a XLSX/CSV.

Uso típico:

    from tools.reporter import Reporter, DataExporter

    rep = Reporter("Reporte de análisis", use_latex=False)
    rep.add_section("Metodología")
    rep.add_paragraph("Descripción del método.")
    rep.add_table(df)
    rep.save("out/reporte.docx")
    rep.cleanup()
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
import warnings
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence, Union

import pandas as pd

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

try:
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover
    plt = None

# ---------------------------------------------------------------------------
# Paleta institucional (códigos Pantone)
# ---------------------------------------------------------------------------
PALETTE: dict[str, dict[str, str]] = {
    "Neutral Black C": {"CMYK": "77/68/63/76", "RGB": "23/27/30", "HEX": "#161A1D"},
    "7420 C": {"CMYK": "29/98/59/18", "RGB": "156/35/72", "HEX": "#9B2247"},
    "626 C": {"CMYK": "83/39/65/37", "RGB": "30/91/79", "HEX": "#1E5B4F"},
    "1255 C": {"CMYK": "32/46/100/10", "RGB": "166/128/45", "HEX": "#A57F2C"},
    "Cool Gray 7 C": {"CMYK": "43/35/34/01", "RGB": "152/152/154", "HEX": "#98989A"},
    "7421 C": {"CMYK": "42/96/56/48", "RGB": "98/19/51", "HEX": "#611232"},
    "627 C": {"CMYK": "87/51/67/68", "RGB": "0/47/42", "HEX": "#002F2A"},
    "7420 C (Light)": {"CMYK": "10/14/48/0", "RGB": "231/210/149", "HEX": "#E6D194"},
}

# ---------------------------------------------------------------------------
# Estilos tipográficos
# ---------------------------------------------------------------------------
FONTS_STYLES: dict[str, dict[str, Any]] = {
    "Base Font": {"Family": "Noto Sans", "Size": 11, "Weight": "Regular", "Color": "Neutral Black C"},
    "Main Titles": {"Family": "Noto Sans", "Size": 24, "Weight": "Bold", "Color": "Neutral Black C"},
    "Section Titles": {"Family": "Noto Sans", "Size": 18, "Weight": "Bold", "Color": "7420 C"},
    "Sub-Section Titles": {"Family": "Noto Sans", "Size": 14, "Weight": "Bold", "Color": "626 C"},
    "Accents / UI Elements / Dashboards": {"Family": "Noto Sans", "Size": 10, "Weight": "Bold", "Color": "1255 C"},
    "Indicators and Statuses": {"Family": "Noto Sans", "Size": 10, "Weight": "Bold", "Color": "7420 C"},
    "Tables & Graphs (Header)": {
        "Family": "Noto Sans", "Size": 10, "Weight": "Bold",
        "Color": "Neutral Black C", "Background": "Cool Gray 7 C",
    },
    "Tables & Graphs (Body)": {"Family": "Noto Sans", "Size": 9, "Weight": "Regular", "Color": "Neutral Black C"},
    "Figures / Diagrams / Flowcharts (Captions)": {
        "Family": "Noto Sans", "Size": 8, "Weight": "Italic", "Color": "Cool Gray 7 C",
    },
}

# ---------------------------------------------------------------------------
# Utilidades de color
# ---------------------------------------------------------------------------
def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convierte #RRGGBB a (R, G, B)."""
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def get_color_rgb(color_name: str, default_hex: str = "#000000") -> tuple[int, int, int]:
    """Obtiene RGB desde PALETTE; si no existe, usa `default_hex`."""
    info = PALETTE.get(color_name)
    return hex_to_rgb(info["HEX"] if info else default_hex)


def sanitize_latex_name(name: str) -> str:
    """Convierte '7420 C (Light)' → '7420CLight'."""
    return re.sub(r"[^A-Za-z0-9]", "", str(name))


def latex_color_name(color_name: str) -> str:
    return sanitize_latex_name(color_name)


# ---------------------------------------------------------------------------
# Estilos Word
# ---------------------------------------------------------------------------
def apply_font_style(run, style_dict: dict[str, Any]) -> None:
    """Aplica un estilo de FONTS_STYLES a un run de Word."""
    if not style_dict or run is None:
        return
    if "Family" in style_dict:
        run.font.name = style_dict["Family"]
    if "Size" in style_dict:
        run.font.size = Pt(style_dict["Size"])
    if "Color" in style_dict:
        rgb = get_color_rgb(style_dict["Color"])
        run.font.color.rgb = RGBColor(*rgb)
    if style_dict.get("Weight") == "Bold":
        run.bold = True
    elif style_dict.get("Weight") == "Italic":
        run.italic = True


# ---------------------------------------------------------------------------
# Exportador de DataFrames
# ---------------------------------------------------------------------------
class DataExporter:
    """Acumula DataFrames y los exporta a XLSX/CSV para auditoría."""

    def __init__(self) -> None:
        self.tables: dict[str, pd.DataFrame] = {}

    def add_dataframe(self, nombre: str, dataframe: Optional[pd.DataFrame]) -> None:
        if dataframe is None or dataframe.empty:
            return
        self.tables[str(nombre)] = dataframe.copy()

    def save_excel(self, filename: Union[str, Path]) -> Optional[str]:
        if not self.tables:
            return None
        filename = str(filename)
        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            for sheet_name, df in self.tables.items():
                df.to_excel(writer, sheet_name=str(sheet_name)[:31], index=False)
        return filename

    def save_csvs(self, folder_name: Union[str, Path] = "csv_exports") -> list[str]:
        if not self.tables:
            return []
        folder = Path(folder_name)
        folder.mkdir(parents=True, exist_ok=True)
        exported: list[str] = []
        for table_name, df in self.tables.items():
            safe = re.sub(r"[^\w.-]+", "_", str(table_name))
            path = folder / f"{safe}.csv"
            df.to_csv(path, index=False)
            exported.append(str(path.resolve()))
        return exported


# ---------------------------------------------------------------------------
# Reporter unificado
# ---------------------------------------------------------------------------
class Reporter:
    """Generador de reportes en DOCX o LaTeX con interfaz común."""

    def __init__(self, title: str = "Reporte de análisis", use_latex: bool = False) -> None:
        self.title = title
        self.use_latex = use_latex
        self.temp_files: list[str] = []

        if use_latex:
            try:
                from pylatex import Command, Document as LatexDoc, NoEscape
                from pylatex.utils import escape_latex
            except ImportError as e:  # pragma: no cover
                raise ImportError(
                    "pylatex es necesario para reportes LaTeX. "
                    "Instálalo con `pip install pylatex`."
                ) from e

            self._latex_escape = escape_latex
            self._NoEscape = NoEscape
            self.doc = LatexDoc()
            self.doc.preamble.append(Command("usepackage", options=["table"], arguments="xcolor"))
            self.doc.preamble.append(Command("usepackage", "booktabs"))
            for color_name, info in PALETTE.items():
                r, g, b = hex_to_rgb(info["HEX"])
                latex_rgb = f"{{rgb,255:red,{r};green,{g};blue,{b}}}"
                self.doc.preamble.append(
                    Command("definecolor", arguments=[latex_color_name(color_name), latex_rgb])
                )
            self.doc.preamble.append(Command("title", escape_latex(title)))
            self.doc.preamble.append(Command("date", NoEscape(r"\today")))
            self.doc.append(NoEscape(r"\maketitle"))
        else:
            self.doc = Document()
            self.doc.add_heading(title, level=0)

    # ------------------------------------------------------------------
    def _clean_text(self, text: Any) -> str:
        if self.use_latex and isinstance(text, str):
            return self._latex_escape(text)
        return str(text)

    # ------------------------------------------------------------------
    def add_section(self, title: str) -> None:
        if self.use_latex:
            from pylatex import Section
            self.doc.append(Section(title))
        else:
            heading = self.doc.add_heading(title, level=1)
            if heading.runs:
                apply_font_style(heading.runs[0], FONTS_STYLES["Section Titles"])

    def add_subsection(self, subtitle: str, text: str = "") -> None:
        if self.use_latex:
            from pylatex import Subsection
            self.doc.append(Subsection(subtitle))
            if text:
                self.doc.append(self._clean_text(text))
        else:
            heading = self.doc.add_heading(subtitle, level=2)
            if heading.runs:
                apply_font_style(heading.runs[0], FONTS_STYLES["Sub-Section Titles"])
            if text:
                self.add_paragraph(text)

    def add_paragraph(self, text: str) -> None:
        if self.use_latex:
            self.doc.append(self._clean_text(text))
        else:
            p = self.doc.add_paragraph()
            run = p.add_run(str(text))
            apply_font_style(run, FONTS_STYLES["Base Font"])

    def add_list(self, items: Iterable[str]) -> None:
        if self.use_latex:
            from pylatex import Itemize
            with self.doc.create(Itemize()) as itemize:
                for item in items:
                    itemize.add_item(self._clean_text(item))
        else:
            for item in items:
                self.doc.add_paragraph(str(item), style="List Bullet")

    # ------------------------------------------------------------------
    def add_image(
        self,
        path: Optional[Union[str, Path]] = None,
        figure_obj: Any = None,
        caption: Optional[str] = None,
        width: float = 5,
        display_in_notebook: bool = True,
    ) -> None:
        image_path = str(path) if path else None

        if figure_obj is not None and plt is not None:
            suffix = ".pdf" if self.use_latex else ".png"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                image_path = tmp.name
            figure_obj.savefig(image_path, bbox_inches="tight")
            self.temp_files.append(image_path)
            plt.close(figure_obj)

        if not image_path or not os.path.exists(image_path):
            print(f"⚠️ Imagen no encontrada: {image_path}")
            return

        if not self.use_latex:
            self.doc.add_picture(image_path, width=Inches(width))
            if caption:
                p = self.doc.add_paragraph()
                run = p.add_run(str(caption))
                apply_font_style(run, FONTS_STYLES["Figures / Diagrams / Flowcharts (Captions)"])
        else:
            from pylatex import Figure, NoEscape
            with self.doc.create(Figure(position="h!")) as fig:
                fig.add_image(image_path, width=NoEscape(f"{width / 6.5}\\textwidth"))
                if caption:
                    fig.add_caption(self._latex_escape(caption))

        if display_in_notebook and not self.use_latex and "IPython" in sys.modules:
            try:
                from IPython.display import Image, display
                display(Image(filename=image_path, width=int(width * 96)))
            except Exception as e:  # pragma: no cover
                warnings.warn(f"No se pudo mostrar la imagen: {e}")

    # ------------------------------------------------------------------
    def add_table(self, data: Union[pd.DataFrame, Sequence], headers: Optional[Sequence[str]] = None) -> None:
        if isinstance(data, pd.DataFrame):
            headers = list(data.columns) if headers is None else headers
            rows = data.to_dict(orient="records")
        else:
            rows = list(data)

        if headers is None and rows:
            first = rows[0]
            headers = list(first.keys()) if isinstance(first, dict) else [f"Columna {i+1}" for i in range(len(first))]
        headers = list(headers or [])

        if self.use_latex:
            from pylatex import NoEscape, Table, Tabular
            from pylatex.utils import escape_latex
            color_name = latex_color_name(FONTS_STYLES["Tables & Graphs (Header)"]["Background"])
            with self.doc.create(Table(position="h!")) as table_env:
                with table_env.create(Tabular("c" * len(headers))) as tabular:
                    tabular.append(NoEscape(r"\toprule"))
                    tabular.append(NoEscape(f"\\rowcolor{{{color_name}}}"))
                    tabular.add_row([NoEscape(rf"\textbf{{{escape_latex(str(h))}}}") for h in headers])
                    tabular.append(NoEscape(r"\midrule"))
                    for row in rows:
                        values = (
                            [escape_latex(str(row.get(h, ""))) for h in headers]
                            if isinstance(row, dict)
                            else [escape_latex(str(v)) for v in row]
                        )
                        tabular.add_row(values)
                    tabular.append(NoEscape(r"\bottomrule"))
        else:
            table = self.doc.add_table(rows=1, cols=len(headers))
            table.style = "Table Grid"
            header_style = FONTS_STYLES["Tables & Graphs (Header)"]
            bg_rgb = get_color_rgb(header_style["Background"])
            hex_fill = f"{bg_rgb[0]:02X}{bg_rgb[1]:02X}{bg_rgb[2]:02X}"

            for i, header in enumerate(headers):
                cell = table.rows[0].cells[i]
                cell.text = str(header)
                if cell.paragraphs[0].runs:
                    apply_font_style(cell.paragraphs[0].runs[0], header_style)
                tcPr = cell._tc.get_or_add_tcPr()
                shade = OxmlElement("w:shd")
                shade.set(qn("w:val"), "clear")
                shade.set(qn("w:fill"), hex_fill)
                tcPr.append(shade)
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

            body_style = FONTS_STYLES["Tables & Graphs (Body)"]
            for row_data in rows:
                cells = table.add_row().cells
                for i, h in enumerate(headers):
                    value = row_data.get(h, "") if isinstance(row_data, dict) else (row_data[i] if i < len(row_data) else "")
                    cells[i].text = str(value)
                    if cells[i].paragraphs[0].runs:
                        apply_font_style(cells[i].paragraphs[0].runs[0], body_style)

    # ------------------------------------------------------------------
    def register_action(self, title: str, inputs: dict, result_df: pd.DataFrame | None = None) -> None:
        self.add_subsection(title)
        if inputs:
            self.add_paragraph("Provided inputs:")
            self.add_list([f"{k}: {v}" for k, v in inputs.items()])
        if result_df is not None and not result_df.empty:
            self.add_paragraph("Result:")
            self.add_table(result_df)

    # ------------------------------------------------------------------
    def save(self, filename: Union[str, Path]) -> None:
        base = str(filename).replace(".tex", "").replace(".pdf", "").replace(".docx", "")
        if self.use_latex:
            self.doc.generate_tex(base)
        else:
            self.doc.save(f"{base}.docx")

    def cleanup(self) -> None:
        for path in self.temp_files:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass
        self.temp_files.clear()
