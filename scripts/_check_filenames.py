#!/usr/bin/env python3
"""Verifica que los nombres de archivo y carpeta sigan la convención en inglés.

Reglas:
- Solo ASCII.
- Sin espacios.
- Extensiones permitidas.
- Palabras en inglés (lista blanca mínima; el resto se reporta como advertencia).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

EXTENSIONS = {
    ".py", ".md", ".yaml", ".yml", ".toml", ".json", ".html", ".css", ".js",
    ".j2", ".tex", ".txt", ".cfg", ".ini", ".env", ".example", ".gitkeep",
    ".ipynb",
}

PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")

SPANISH_WORDS = {
    "manual", "informe", "arquitectura", "privacidad", "juramento",
    "despliegue", "agentes", "roles", "soberano", "instalacion",
    "edges", "ejemplo", "semilla", "contrato", "bitacora",
}


def check(path: Path) -> list[str]:
    errors: list[str] = []
    name = path.name
    if path.is_dir():
        if not PATTERN.match(name):
            errors.append(f"{path}: nombre de carpeta no válido")
        return errors
    if path.suffix.lower() not in EXTENSIONS and not name.startswith(".env"):
        return errors
    if not PATTERN.match(name):
        errors.append(f"{path}: nombre de archivo no válido (ASCII, sin espacios)")
    base = path.stem.lower().replace("-", "_").split("_")[0]
    if base in SPANISH_WORDS:
        errors.append(f"{path}: posible nombre en español (convención: inglés)")
    return errors


def main(argv: list[str]) -> int:
    errors: list[str] = []
    for arg in argv:
        errors.extend(check(Path(arg)))
    for e in errors:
        print(e, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
