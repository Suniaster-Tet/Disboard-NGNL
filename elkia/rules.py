"""Reglas del tablero y validaciones de Elkia.

Las reglas operativas se derivan del README (Juramento Soberano y requisitos
de arquitectura). Este módulo no impone las Diez Reglas como código de juego,
sino que valida que un edge cumpla los mínimos para operar.
"""
from __future__ import annotations

from typing import Dict, List

from core.contract import Contract
from core.edge import Edge


class BoardRules:
    """Validaciones mínimas para que un edge pueda ejecutarse."""

    @staticmethod
    def validar_creacion(edge: Edge) -> List[str]:
        errores: List[str] = []
        if not edge.id:
            errores.append("El edge debe tener un ID.")
        if not edge.ruta.exists():
            errores.append(f"La ruta del edge no existe: {edge.ruta}")
        return errores

    @staticmethod
    def validar_aprobacion(edge: Edge, contract: Contract) -> List[str]:
        errores: List[str] = []
        if not contract.aprobado_por_tet:
            errores.append("El contrato no ha sido aprobado por Tet.")
        if not contract.firma_tet:
            errores.append("El contrato no tiene firma HMAC de Tet.")
        return errores

    @staticmethod
    def validar_ejecucion(edge: Edge, contract: Contract) -> List[str]:
        errores: List[str] = []
        errores.extend(BoardRules.validar_aprobacion(edge, contract))
        if not contract.objetivos:
            errores.append("El contrato no tiene objetivos definidos.")
        if not contract.entregables:
            errores.append("El contrato no tiene entregables definidos.")
        if edge.estado not in {"NUEVO", "EN_PROCESO"}:
            errores.append(f"Estado no válido para ejecución: {edge.estado}")
        return errores

    @staticmethod
    def validar_cierre(edge: Edge, contract: Contract) -> List[str]:
        errores: List[str] = []
        if edge.estado != "EN_REVISION":
            errores.append("Solo se puede cerrar un edge en revisión.")
        if edge.avance < 100:
            errores.append(f"Avance insuficiente para cierre: {edge.avance}%")
        if contract.validar():
            errores.extend(contract.validar())
        return errores

    @staticmethod
    def validar_rollback(edge: Edge) -> List[str]:
        errores: List[str] = []
        if edge.estado == "EN_REVISION" and edge.avance > 0:
            errores.append(
                "Un edge en revisión con avance > 0 requiere un rollback registrado."
            )
        return errores

    @staticmethod
    def resumen(errores: List[str]) -> Dict[str, object]:
        return {"ok": not errores, "errores": errores}
