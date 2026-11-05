"""Comandos de Elkia expuestos a través de `console.main`."""
from __future__ import annotations

import argparse
import json
import sys

from elkia.dashboard import ElkiaDashboard
from elkia.registry import ElkiaRegistry
from elkia.rules import BoardRules
from core.contract import Contract
from core.edge import Edge


def cmd_status(verbose: bool = False) -> int:
    registro = ElkiaRegistry()
    edges = registro.listar()
    if not edges:
        print("✔ No hay partidas activas. Matriz de Eisenhower en equilibrio.")
        return 0

    print(f"➜ {len(edges)} edge(s) activo(s):")
    for e in edges:
        print(
            f"  - {e.id} | avance: {e.avance:>3}% | "
            f"prioridad: {e.prioridad} | estado: {e.estado}"
        )
    if verbose:
        resumen = registro.resumen()
        print("  Resumen:", json.dumps(resumen, ensure_ascii=False))
    return 0


def cmd_dashboard(as_json: bool = False) -> int:
    dashboard = ElkiaDashboard()
    if as_json:
        print(dashboard.render_json())
    else:
        print(dashboard.render_markdown())
    return 0


def cmd_list_edges(as_json: bool = False) -> int:
    registro = ElkiaRegistry()
    meta = registro.listar_meta()
    if as_json:
        print(json.dumps(meta, ensure_ascii=False, indent=2))
    else:
        for edge_id, info in meta.items():
            print(f"{edge_id} | {info.get('titulo', '')} | {info.get('estado', '')}")
    return 0


def cmd_check_contract(edge_id: str) -> int:
    try:
        edge = Edge.cargar(edge_id)
    except FileNotFoundError:
        print(f"✖ Edge no encontrado: {edge_id}", file=sys.stderr)
        return 2
    if not edge.ruta_contrato.exists():
        print(f"✖ Contrato no encontrado: {edge.ruta_contrato}", file=sys.stderr)
        return 2
    contract = Contract.cargar(edge.ruta_contrato)
    errores = BoardRules.validar_ejecucion(edge, contract)
    if errores:
        for e in errores:
            print(f"✖ {e}", file=sys.stderr)
        return 1
    print(f"✔ Contrato válido para ejecución: {edge_id}")
    return 0


def build_subparser(sub: argparse._SubParsersAction) -> None:
    p_status = sub.add_parser("status", help="Estado global de Elkia")
    p_status.add_argument("--verbose", action="store_true")
    p_status.set_defaults(func=lambda a: cmd_status(a.verbose))

    p_dash = sub.add_parser("dashboard", help="Tablero de control de Elkia")
    p_dash.add_argument("--json", action="store_true", dest="as_json")
    p_dash.set_defaults(func=lambda a: cmd_dashboard(a.as_json))

    p_list = sub.add_parser("list-edges", help="Lista edges con metadatos")
    p_list.add_argument("--json", action="store_true", dest="as_json")
    p_list.set_defaults(func=lambda a: cmd_list_edges(a.as_json))

    p_check = sub.add_parser("check-contract", help="Valida el contrato de un edge")
    p_check.add_argument("edge_id")
    p_check.set_defaults(func=lambda a: cmd_check_contract(a.edge_id))
