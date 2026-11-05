"""Suniaster: núcleo de asignación y actualización de modelos de IA."""

__version__ = "2.0.0"

from suniaster.providers import (
    ProviderUnavailable,
    create_model,
    list_supported_providers,
)
from suniaster.router import SuniasterRouter
from suniaster.updater import SuniasterUpdater

__all__ = [
    "SuniasterRouter",
    "SuniasterUpdater",
    "create_model",
    "ProviderUnavailable",
    "list_supported_providers",
]
