"""Ejecutor de pruebas unitarias (unittest) para el flujo TDD de Shiro."""
from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any, Dict


class TestRunner:
    def __init__(self, test_dir: str = "tests"):
        self.test_dir = Path(test_dir)

    def run_suite(self) -> Dict[str, Any]:
        """Descubre y ejecuta la suite de pruebas unitarias focalizadas."""
        loader = unittest.TestLoader()
        suite = loader.discover(start_dir=str(self.test_dir), pattern="test_*.py")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return {
            "status": "success" if result.wasSuccessful() else "failure",
            "tests_run": result.testsRun,
            "errors": len(result.errors),
            "failures": len(result.failures),
        }
