"""Fiel Nirvalen: reexporta el filtro central de privacidad.

El filtro real vive en `privacy/filters.py`. Este módulo solo existe para
mantener la API pública que ya usan los agentes (`filter_sensitive_data`,
`filter_dict`, `is_safe`) sin duplicar patrones.
"""
from privacy.filters import filter_dict, filter_sensitive_data, is_safe

__all__ = ["filter_sensitive_data", "filter_dict", "is_safe"]
