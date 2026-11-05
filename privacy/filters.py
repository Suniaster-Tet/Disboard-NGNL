"""Filtros de privacidad centralizados de Disboard-NGNL.

Este módulo es la fuente de verdad de los patrones de datos sensibles.
`agents/fiel_nirvalen/privacy_filter.py` reexporta desde aquí para no duplicar
lógica.

Si `PRIVACY_STRICT=true` (por defecto), se aplican todos los patrones. Si
`PRIVACY_STRICT=false`, solo se aplican los patrones mínimos (email, teléfono,
tarjeta).
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict

# --- Patrones base (siempre activos) ---
_BASE_PATTERNS = [
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[EMAIL_PROTECTED]"),
    (re.compile(r"\b\d{3}[- ]?\d{3}[- ]?\d{3}[- ]?\d{3}\b"), "[PHONE_PROTECTED]"),
    (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), "[CARD_PROTECTED]"),
]

# --- Patrones extra (solo si PRIVACY_STRICT != "false") ---
_EXTRA_PATTERNS = [
    (re.compile(r"\b\d{2}[.-]?\d{3}[.-]?\d{3}[.-]?[A-Z]\b"), "[DNI_PROTECTED]"),
    (re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b"), "[IBAN_PROTECTED]"),
    (re.compile(r"https?://\S+[?&](?:token|key|auth)=\S+"), "[URL_WITH_TOKEN]"),
]


def _strict_enabled() -> bool:
    return os.getenv("PRIVACY_STRICT", "true").lower() not in {"false", "0", "no"}


def filter_sensitive_data(text: str) -> str:
    """Filtra datos sensibles antes de cualquier prompt externo o log."""
    if not isinstance(text, str):
        return text
    for pattern, replacement in _BASE_PATTERNS:
        text = pattern.sub(replacement, text)
    if _strict_enabled():
        for pattern, replacement in _EXTRA_PATTERNS:
            text = pattern.sub(replacement, text)
    return text


def filter_prompt_external(text: str) -> str:
    """Filtra datos sensibles antes de enviar un prompt a una API externa.

    Es equivalente a `filter_sensitive_data`, pero semánticamente deja claro
    que el texto va a salir del host.
    """
    return filter_sensitive_data(text)


def filter_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Aplica el filtro a todos los valores string de un diccionario."""
    return {
        k: filter_sensitive_data(v) if isinstance(v, str) else v
        for k, v in data.items()
    }


def is_safe(text: str) -> bool:
    """Devuelve True si el texto no contiene patrones sensibles."""
    if not isinstance(text, str):
        return True
    for pattern, _ in _BASE_PATTERNS:
        if pattern.search(text):
            return False
    if _strict_enabled():
        for pattern, _ in _EXTRA_PATTERNS:
            if pattern.search(text):
                return False
    return True
