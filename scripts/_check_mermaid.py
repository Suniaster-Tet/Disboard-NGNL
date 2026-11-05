#!/usr/bin/env python3
"""Verifica que todos los bloques Mermaid en Markdown abran y cierren correctamente."""
from __future__ import annotations

import re
import sys
from pathlib import Path

FENCE_OPEN = re.compile(r"^```mermaid\s*$")
FENCE_CLOSE = re.compile(r"^```\s*$")


def check_file(path: Path) -> list[str]:
    errores: list[str] = []
    abierto = False
    inicio = 0
    for i, linea in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not abierto and FENCE_OPEN.match(linea):
            abierto = True
            inicio = i
        elif abierto and FENCE_CLOSE.match(linea):
            abierto = False
    if abierto:
        errores.append(f"{path}:{inicio}: bloque Mermaid sin cerrar")
    return errores


def main(argv: list[str]) -> int:
    errores: list[str] = []
    for arg in argv:
        errores.extend(check_file(Path(arg)))
    for e in errores:
        print(e, file=sys.stderr)
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
