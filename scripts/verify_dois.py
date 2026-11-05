#!/usr/bin/env python3
"""Verificación masiva de DOIs con Jibril.

Lee una lista de DOIs (archivo de texto, uno por línea o separados por comas)
y verifica cada uno contra Crossref, OpenAlex y ORCID. Genera un reporte
JSONL con el resultado de la verificación.

Uso:
    python scripts/verify_dois.py --input dois.txt --output doi_verification.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.jibril.agent import JibrilScientific
from agents.jibril.crossref_client import CrossrefClient
from agents.jibril.doi_verifier import verify_doi
from agents.jibril.openalex_client import OpenAlexClient
from agents.jibril.orcid_client import OrcidClient


def _read_dois(path: Path) -> list[str]:
    """Lee DOIs de un archivo (uno por línea o separados por comas)."""
    text = path.read_text(encoding="utf-8")
    candidates: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for part in line.split(","):
            part = part.strip()
            if part:
                candidates.append(part)
    return candidates


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verificación masiva de DOIs con Jibril."
    )
    parser.add_argument("--input", type=Path, required=True,
                        help="Archivo con DOIs (uno por línea o separados por comas)")
    parser.add_argument("--output", type=Path, default=Path("doi_verification.jsonl"),
                        help="Archivo JSONL de salida")
    parser.add_argument("--edge", type=str, default="edge-verification",
                        help="Edge asociado (para el log)")
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"✖ No se encontró el archivo de entrada: {args.input}", file=sys.stderr)
        return 2

    dois = _read_dois(args.input)
    if not dois:
        print("✖ No se encontraron DOIs en el archivo de entrada.", file=sys.stderr)
        return 2

    print(f"➜ Verificando {len(dois)} DOI(s) con Jibril...")

    jibril = JibrilScientific(edge_id=args.edge)
    crossref = CrossrefClient()
    openalex = OpenAlexClient()
    orcid = OrcidClient()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    ok = 0
    failed = 0

    with args.output.open("w", encoding="utf-8") as f:
        for doi in dois:
            result = verify_doi(doi, crossref, openalex, orcid)
            if result["ok"]:
                ok += 1
                entry = {
                    "doi": doi,
                    "verified": True,
                    "source": result["source"],
                    "title": result["metadata"].get("title", ""),
                    "metadata": result["metadata"],
                }
            else:
                failed += 1
                entry = {
                    "doi": doi,
                    "verified": False,
                    "reason": result["reason"],
                }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            status = "✔" if result["ok"] else "✖"
            print(f"  {status} {doi}")

    print(f"\n✔ Verificados: {ok}")
    print(f"✖ Fallidos: {failed}")
    print(f"➜ Reporte: {args.output}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
