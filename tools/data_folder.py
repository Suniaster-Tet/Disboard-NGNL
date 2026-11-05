"""Detección e inspección de carpetas fuente y READMEs.

Complementa a `tools/data_loader.py`.
"""
from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd

VALID_EXTENSIONS = (".xlsx", ".xls", ".csv", ".docx", ".pdf")
MAX_README_DEPTH = 2


def parse_readme(path: Path) -> dict[str, Any]:
    """Extrae metadatos relevantes de un README.md."""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "path": str(path),
            "error": str(e),
            "verified_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    data: dict[str, Any] = {
        "path": str(path),
        "verified_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    m = re.search(r"_Last update:\s*(\d{2}/\d{2}/\d{4})_", content)
    data["last_update"] = m.group(1) if m else "Not specified"

    m = re.search(r"\*\*File:\*\*\s*([^\n]+(?:\.csv|\.xlsx|\.xls|\.pdf|\.docx))", content)
    data["declared_file"] = m.group(1).strip() if m else "Not declared"

    data["preview"] = content[:500] + "..." if len(content) > 500 else content
    return data


def scan_folder(folder: Path) -> dict[str, Any]:
    """Escanea una carpeta recursivamente buscando archivos válidos y READMEs."""
    if not folder.exists():
        return {"error": f"Path does not exist: {folder}", "files": [], "readmes": []}

    files: list[Path] = []
    readmes: list[dict[str, Any]] = []

    for root, _, filenames in os.walk(folder):
        root_path = Path(root)
        depth = len(root_path.relative_to(folder).parts)

        if "README.md" in filenames and depth <= MAX_README_DEPTH:
            readmes.append(parse_readme(root_path / "README.md"))

        for filename in filenames:
            if filename.startswith("~$"):
                continue
            if filename.lower().endswith(VALID_EXTENSIONS):
                files.append(root_path / filename)

    return {"files": files, "readmes": readmes}


def scan_folder_interactive(reporters: Optional[list] = None) -> tuple[Optional[Path], list[Path]]:
    """Versión interactiva que registra resultados en los reporteros."""
    if reporters is None:
        reporters = []

    raw = input("Folder path to scan: ").strip().strip('"').strip("'")
    folder = Path(raw)

    result = scan_folder(folder)
    if "error" in result:
        print(f"❌ {result['error']}")
        return None, []

    files = result["files"]
    readmes = result["readmes"]
    print(f"\n✅ {len(files)} valid file(s) and {len(readmes)} README(s) detected.")

    for r in reporters:
        if hasattr(r, "register_action"):
            r.register_action(
                title="Source folder detection",
                inputs={
                    "Path": str(folder),
                    "Valid files": len(files),
                    "READMEs": len(readmes),
                },
                result_df=pd.DataFrame({"file": [str(a.relative_to(folder)) for a in files]}),
            )

    return folder, files
