"""Read and update the active project registry in Elkia.md."""
from __future__ import annotations

import re
import tempfile
from datetime import date
from pathlib import Path


REGISTRY_START = "<!-- REGISTRO_PROYECTOS_INICIO -->"
REGISTRY_END = "<!-- REGISTRO_PROYECTOS_FIN -->"
TABLE_HEADERS = (
    "ID del Proyecto",
    "Carpeta Edge",
    "Título y Enfoque",
    "Estado",
    "Avance Global (%)",
    "Último hito / movimiento",
    "Siguiente acción",
    "Última actualización",
    "Responsable",
    "Contrato",
    "Peticiones",
)


def read_master_index(master_path: str | Path) -> str:
    path = Path(master_path)
    if path.is_symlink():
        raise ValueError("Elkia.md no puede ser un enlace simbólico.")
    content = path.read_text(encoding="utf-8")
    if REGISTRY_START not in content or REGISTRY_END not in content:
        raise ValueError("Elkia.md no contiene los marcadores del registro maestro.")
    required_sections = (
        "## 🏛️ Directrices de Arquitectura y Gobernanza",
        "## 🧩 Arquitectura de Skills",
        "## 🏛️ Directrices de Ejecución para los Agentes",
        "### Capacidades principales implementadas y límites actuales",
        "## ⚖️ Delegación y Matriz de Autorizaciones",
        "## 🗂️ Convenciones de Estado de Proyectos",
    )
    missing = [section for section in required_sections if section not in content]
    if missing:
        raise ValueError(
            "Elkia.md está incompleto; faltan secciones operativas: "
            + ", ".join(missing)
        )
    return content


def agent_index_context(content: str) -> str:
    """Return global policy, agent roles, active projects, and status rules."""
    def section(title: str, next_title: str) -> str:
        parts = content.split(title, 1)
        if len(parts) != 2:
            return ""
        body = parts[1].split(next_title, 1)
        if len(body) != 2:
            return ""
        return title + body[0].strip()

    header = content.split("## 🏛️ Directrices de Arquitectura y Gobernanza", 1)[0]
    governance = section(
        "## 🏛️ Directrices de Arquitectura y Gobernanza",
        "## 🧩 Arquitectura de Skills",
    )
    skills_roles_and_capabilities = section(
        "## 🧩 Arquitectura de Skills",
        "## 🛠️ Pool de Herramientas",
    )
    delegation = section(
        "## ⚖️ Delegación y Matriz de Autorizaciones",
        "---",
    )

    active_registry = ""
    if REGISTRY_START in content and REGISTRY_END in content:
        table = content.split(REGISTRY_START, 1)[1].split(REGISTRY_END, 1)[0]
        table_lines = []
        in_table = False
        for line in table.splitlines():
            if line.startswith("|"):
                in_table = True
                table_lines.append(line)
            elif in_table:
                break
        active_registry = (
            "## 📊 Edges activos en Elkia.md\n" + "\n".join(table_lines)
        )
    conventions = section(
        "## 🗂️ Convenciones de Estado de Proyectos",
        "## 📦 Convenciones de Formato",
    )
    segments = (
        header,
        governance,
        skills_roles_and_capabilities,
        delegation,
        active_registry,
        conventions,
    )
    return "\n\n".join(segment.strip() for segment in segments if segment.strip()) or content


def _table_lines(content: str) -> tuple[list[str], int, int]:
    start = content.index(REGISTRY_START) + len(REGISTRY_START)
    end = content.index(REGISTRY_END, start)
    lines = content[start:end].splitlines()
    header_index = next(
        (
            index
            for index, line in enumerate(lines)
            if line.startswith("|") and "ID del Proyecto" in line
        ),
        None,
    )
    if header_index is None:
        raise ValueError("Elkia.md no contiene la tabla del registro de proyectos.")
    table_end = header_index + 1
    while table_end < len(lines) and lines[table_end].startswith("|"):
        table_end += 1
    return lines, header_index, table_end


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _plain(value: str) -> str:
    return value.strip().strip("*").strip("`").strip()


def project_records(content: str) -> list[dict[str, str]]:
    lines, header_index, table_end = _table_lines(content)
    headers = [_plain(cell).casefold() for cell in _cells(lines[header_index])]
    records = []
    for line in lines[header_index + 1:table_end]:
        cells = _cells(line)
        if not cells or all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells):
            continue
        if len(cells) < 5:
            continue
        values = dict(zip(headers, cells))
        folder = _plain(values.get("carpeta edge", values.get("carpeta del proyecto", "")))
        records.append({
            "id": _plain(values.get("id del proyecto", "")),
            "slug": folder,
            "title": _plain(values.get("título y enfoque", values.get("título y enfoque estratégico", ""))),
            "status": _plain(values.get("estado", "")),
            "progress": _plain(values.get("avance global (%)", "")),
            "milestone": _plain(values.get("último hito / movimiento", "")),
            "next_action": _plain(values.get("siguiente acción", "")),
            "updated": _plain(values.get("última actualización", "")),
            "responsible": _plain(values.get("responsable", values.get("responsable técnico", ""))),
            "contract": _plain(values.get("contrato", "")),
            "requests": _plain(values.get("peticiones", "")),
        })
    return records


def project_by_id(content: str, project_id: str) -> dict[str, str] | None:
    wanted = project_id.strip().casefold()
    return next((record for record in project_records(content)
                 if record["id"].casefold() == wanted), None)


def project_by_slug(content: str, slug: str) -> dict[str, str] | None:
    wanted = slug.strip().casefold()
    return next((record for record in project_records(content)
                 if record["slug"].strip("`").casefold() == wanted), None)


def render_project_table(records: list[dict[str, str]]) -> str:
    lines = [
        "| " + " | ".join(TABLE_HEADERS) + " |",
        "| " + " | ".join(":---" for _ in TABLE_HEADERS) + " |",
    ]
    fields = (
        "id", "slug", "title", "status", "progress", "milestone", "next_action",
        "updated", "responsible", "contract", "requests",
    )
    for record in records:
        values = [record.get(field, "") for field in fields]
        values[0] = f"**{_plain(values[0])}**"
        values[1] = f"`{_plain(values[1])}`"
        values[8] = _plain(values[8])
        values[9] = f"`{_plain(values[9])}`"
        values[10] = f"`{_plain(values[10])}`"
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def _normalized_records(content: str) -> list[dict[str, str]]:
    return [
        {
            **record,
            "milestone": record["milestone"] or "Sin movimiento registrado",
            "next_action": record["next_action"] or "Tet/Sora: revisar el contrato",
        }
        for record in project_records(content)
    ]


def register_project_content(
    content: str, project_id: str, slug: str, title: str
) -> str:
    records = _normalized_records(content)
    if any(record["id"].casefold() == project_id.casefold() for record in records):
        return content
    if any(record["slug"].casefold() == slug.casefold() for record in records):
        raise ValueError(f"La carpeta ya está registrada en Elkia.md: {slug}")
    records.append({
        "id": project_id,
        "slug": slug,
        "title": title,
        "status": "NUEVO",
        "progress": "0%",
        "milestone": "Edge creado; contrato pendiente de revisión",
        "next_action": "Tet: revisar objetivos y aprobar contract.md",
        "updated": date.today().isoformat(),
        "responsible": "Sora",
        "contract": "contract.md",
        "requests": "docs/peticiones_tet.md",
    })
    return _write_table(content, records)


def _write_table(content: str, records: list[dict[str, str]]) -> str:
    lines, header_index, table_end = _table_lines(content)
    lines[header_index:table_end] = render_project_table(records).splitlines()
    start = content.index(REGISTRY_START) + len(REGISTRY_START)
    end = content.index(REGISTRY_END, start)
    return content[:start] + "\n".join(lines) + content[end:]


def _atomic_write(path: Path, content: str) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with open(descriptor, "w", encoding="utf-8", newline="") as output:
            output.write(content)
            output.flush()
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def register_project(
    master_path: str | Path, project_id: str, slug: str, title: str
) -> None:
    path = Path(master_path)
    content = read_master_index(path)
    updated_content = register_project_content(content, project_id, slug, title)
    if updated_content == content:
        raise ValueError(f"El ID ya existe en Elkia.md: {project_id}")
    _atomic_write(path, updated_content)


def update_project(
    master_path: str | Path,
    slug: str,
    *,
    status: str | None = None,
    milestone: str | None = None,
    next_action: str | None = None,
    progress: str | None = None,
    responsible: str | None = None,
) -> None:
    path = Path(master_path)
    content = read_master_index(path)
    records = _normalized_records(content)
    record = next((item for item in records if item["slug"].strip("`").casefold() == slug.casefold()), None)
    if record is None:
        raise LookupError(f"El proyecto no está registrado en Elkia.md: {slug}")
    if status is not None:
        record["status"] = status
    if milestone is not None:
        record["milestone"] = milestone
    if next_action is not None:
        record["next_action"] = next_action
    if progress is not None:
        record["progress"] = progress
    if responsible is not None:
        record["responsible"] = responsible
    record["updated"] = date.today().isoformat()
    _atomic_write(path, _write_table(content, records))
