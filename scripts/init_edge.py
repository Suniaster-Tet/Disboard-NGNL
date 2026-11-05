#!/usr/bin/env python3
"""Crea un edge-* con su contrato inicial a partir de una idea semilla.

Uso:
    python scripts/init_edge.py --seed ruta/a/idea.md --titulo "Mi proyecto"

Requiere que las variables de entorno del proyecto estén configuradas
(ver `.env.example`).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Asegurar que el paquete raíz sea importable al ejecutar el script directamente
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.contract import Contract
from core.edge import Edge
from core.log import Log
from elkia.registry import ElkiaRegistry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Crea un edge-* con su contrato inicial en Disboard-NGNL."
    )
    parser.add_argument("--seed", type=Path, default=None,
                        help="Ruta al archivo de idea semilla (.md)")
    parser.add_argument("--titulo", type=str, default=None,
                        help="Título legible del edge (por defecto: nombre del archivo semilla)")
    args = parser.parse_args(argv)

    if args.seed and not args.seed.exists():
        print(f"✖ No se encontró la idea semilla: {args.seed}", file=sys.stderr)
        return 2

    edge = Edge.crear_desde_semilla(args.seed, titulo=args.titulo)

    contract = Contract(edge_id=edge.id)
    contract.guardar(edge.ruta_contrato)

    registry = ElkiaRegistry()
    registry.registrar(edge)

    Log(edge.id).registrar(
        "edge_created",
        {"seed": str(args.seed) if args.seed else None, "title": edge.titulo},
        agente="Tet",
    )

    print(f"✔ Edge creado: {edge.id}")
    print(f"➜ Ruta: {edge.ruta}")
    print(f"➜ Contrato: {edge.ruta_contrato}")
    print(f"➜ Log: {edge.ruta_log}")
    print("✦ ¡Aschente! Sora puede ahora proponer el plan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
