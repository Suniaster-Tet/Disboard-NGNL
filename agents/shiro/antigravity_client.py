"""Cliente opcional de Antigravity para Shiro.

Antigravity NO es exclusivo de Shiro: es una herramienta más que Suniaster
puede habilitar. Si no está disponible, Shiro opera con el proveedor asignado.
"""
from __future__ import annotations

import shutil
import subprocess
from typing import Optional


class AntigravityClient:
    def __init__(self, binary: str = "agy"):
        self.binary = binary

    def is_available(self) -> bool:
        return shutil.which(self.binary) is not None

    def version(self) -> Optional[str]:
        if not self.is_available():
            return None
        try:
            out = subprocess.run(
                [self.binary, "--version"],
                capture_output=True, text=True, timeout=10, check=False,
            )
            return out.stdout.strip() or None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def run(self, prompt: str, timeout: int = 60) -> Optional[str]:
        if not self.is_available():
            return None
        try:
            out = subprocess.run(
                [self.binary, "--prompt", prompt],
                capture_output=True, text=True, timeout=timeout, check=False,
            )
            return out.stdout.strip() or None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None
