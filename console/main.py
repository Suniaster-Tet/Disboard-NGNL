#!/usr/bin/env python3
"""CLI principal de Disboard-NGNL (entrypoint: `disboard`)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from console import commands
from console.presentation import Presentation
from core.contract import Contract
from core.edge import Edge
from elkia.dashboard import ElkiaDashboard
from elkia.registry import ElkiaRegistry
from elkia.rules import BoardRules
from suniaster.updater import SuniasterUpdater


def _cmd_start(args: argparse.Namespace) -> int:
 return commands.start(args.seed, args.titulo)


def _cmd_continue(args: argparse.Namespace) -> int:
 return commands.continue_edge(args.edge_id)


def _cmd_approve(args: argparse.Namespace) -> int:
 return commands.approve(args.edge_id, args.paso)


def _cmd_reject(args: argparse.Namespace) -> int:
 return commands.reject(args.edge_id, args.paso)


def _cmd_check_models(_: argparse.Namespace) -> int:
 print("✦ [Suniaster]: Iniciando inspección de endpoints y modelos...")
 result = SuniasterUpdater().check_and_update()
 print(f"✔ Estado: {result['status']}")
 for agent, det in result["details"].items():
     icon = "✔" if det.get("ok") else "✖"
     print(f"  {icon} {agent}: {det.get('model', det.get('error', '?'))}")
 return 0 if result["status"] == "ok" else 1


def _cmd_status(_: argparse.Namespace) -> int:
 edges = ElkiaRegistry().listar()
 Presentation.show_status(edges)
 return 0


def _cmd_dashboard(args: argparse.Namespace) -> int:
 dashboard = ElkiaDashboard()
 if args.as_json:
     Presentation.show_dashboard(dashboard.render_json())
 else:
     Presentation.show_dashboard(dashboard.render_markdown())
 return 0


def _cmd_list_edges(args: argparse.Namespace) -> int:
 meta = ElkiaRegistry().listar_meta()
 if args.as_json:
     import json
     print(json.dumps(meta, ensure_ascii=False, indent=2))
 else:
     for edge_id, info in meta.items():
         print(f"{edge_id} | {info.get('titulo', '')} | {info.get('estado', '')}")
 return 0


def _cmd_check_contract(args: argparse.Namespace) -> int:
 try:
     edge = Edge.cargar(args.edge_id)
 except FileNotFoundError:
     print(f"✖ Edge no encontrado: {args.edge_id}", file=sys.stderr)
     return 2
 if not edge.ruta_contrato.exists():
     print(f"✖ Contrato no encontrado: {edge.ruta_contrato}", file=sys.stderr)
     return 2
 contract = Contract.cargar(edge.ruta_contrato)
 errors = BoardRules.validar_ejecucion(edge, contract)
 if errors:
     for e in errors:
         print(f"✖ {e}", file=sys.stderr)
     return 1
 print(f"✔ Contrato válido para ejecución: {args.edge_id}")
 return 0


def build_parser() -> argparse.ArgumentParser:
 parser = argparse.ArgumentParser(
     prog="disboard",
     description="✦ Disboard-NGNL: Tablero Multiagente de Investigación Científica ✦",
 )
 sub = parser.add_subparsers(dest="command", required=True)

 p_start = sub.add_parser("start", help="Iniciar un nuevo edge")
 p_start.add_argument("--seed", type=Path, default=None)
 p_start.add_argument("--titulo", type=str, default=None)
 p_start.set_defaults(func=_cmd_start)

 p_cont = sub.add_parser("continue", help="Continuar un edge existente")
 p_cont.add_argument("edge_id")
 p_cont.set_defaults(func=_cmd_continue)

 p_app = sub.add_parser("approve", help="Aprobar un paso del edge")
 p_app.add_argument("edge_id")
 p_app.add_argument("--paso", default="final")
 p_app.set_defaults(func=_cmd_approve)

 p_rej = sub.add_parser("reject", help="Rechazar un paso del edge")
 p_rej.add_argument("edge_id")
 p_rej.add_argument("--paso", default="final")
 p_rej.set_defaults(func=_cmd_reject)

 p_models = sub.add_parser("check-models", help="Inspección de modelos de Suniaster")
 p_models.set_defaults(func=_cmd_check_models)

 p_status = sub.add_parser("status", help="Estado global del tablero")
 p_status.set_defaults(func=_cmd_status)

 p_dash = sub.add_parser("dashboard", help="Tablero de control de Elkia")
 p_dash.add_argument("--json", action="store_true", dest="as_json")
 p_dash.set_defaults(func=_cmd_dashboard)

 p_list = sub.add_parser("list-edges", help="Lista edges con metadatos")
 p_list.add_argument("--json", action="store_true", dest="as_json")
 p_list.set_defaults(func=_cmd_list_edges)

 p_chk = sub.add_parser("check-contract", help="Valida el contrato de un edge")
 p_chk.add_argument("edge_id")
 p_chk.set_defaults(func=_cmd_check_contract)

 return parser


def main(argv: list[str] | None = None) -> int:
 parser = build_parser()
 args = parser.parse_args(argv)
 return args.func(args)


if __name__ == "__main__":
 sys.exit(main())
