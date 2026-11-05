"""Detección de entorno de ejecución (Colab, Codespaces, Jupyter, local)."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any


def detect_environment() -> dict[str, Any]:
    """Detecta el entorno de ejecución actual."""
    is_colab = "google.colab" in sys.modules
    is_codespaces = os.environ.get("CODESPACES") == "true"

    try:
        from IPython import get_ipython
        is_jupyter = get_ipython() is not None
    except Exception:
        is_jupyter = False

    if is_colab:
        environment = "Google Colab"
    elif is_codespaces:
        environment = "GitHub Codespaces"
    elif is_jupyter:
        environment = "Jupyter Notebook"
    else:
        environment = "Local / VS Code / Terminal"

    return {
        "environment": environment,
        "is_colab": is_colab,
        "is_codespaces": is_codespaces,
        "is_jupyter": is_jupyter,
        "cwd": str(Path.cwd()),
        "python_version": sys.version.split()[0],
    }
