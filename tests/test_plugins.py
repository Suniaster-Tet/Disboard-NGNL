"""Pruebas de plugins y almacenamiento de artefactos.

Aplica la Opción A: `plugin.run(root, ...)` recibe `root` como la raíz del
edge. Los artefactos se guardan en `root/artifacts/`.
"""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from core.plugins import (
    CONTRACT_VERSION,
    PluginDescriptor,
    PluginRegistry,
    create_default_registry,
)
from disboard_ext.local_artifact_store import LocalArtifactStore


class LocalArtifactStoreTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.edge_root = Path(self.td.name) / "edges" / "edge-results"
        self.store = LocalArtifactStore(self.edge_root)

    def tearDown(self):
        self.td.cleanup()

    def test_save_and_verify(self):
        content = b"# resultado\n"
        digest = hashlib.sha256(content).hexdigest()
        res = self.store.save_artifact("docs/report.md", content)
        self.assertEqual(res["sha256"], digest)
        self.assertTrue(self.store.verify_artifact("docs/report.md", digest))
        self.assertFalse(self.store.verify_artifact("docs/report.md", "0" * 64))

    def test_list(self):
        self.store.save_artifact("a.txt", b"a")
        items = self.store.list_artifacts()
        self.assertEqual(len(items), 1)


class PluginRegistryTests(unittest.TestCase):
    class Plugin:
        def __init__(self, value):
            self.value = value

        def run(self, *args, **kwargs):
            return self.value

    def test_contract_version(self):
        registry = PluginRegistry()
        d = PluginDescriptor("x", "transform", "1.0.0", CONTRACT_VERSION)
        registry.register(d, self.Plugin("ok"))
        self.assertEqual(registry.get("transform", "x").run(), "ok")

    def test_default_registry_lists_storage(self):
        with tempfile.TemporaryDirectory() as td:
            registry = create_default_registry()
            plugin = registry.get("storage", "local-filesystem")
            self.assertEqual(
                plugin.run(Path(td) / "edges" / "edge-empty", "list"),
                [],
            )

    def test_replacement_requires_opt_in(self):
        registry = PluginRegistry()
        d = PluginDescriptor("x", "transform", "1.0.0", CONTRACT_VERSION)
        registry.register(d, self.Plugin("first"))
        with self.assertRaises(ValueError):
            registry.register(d, self.Plugin("second"))
        registry.register(d, self.Plugin("second"), replace_existing=True)
        self.assertEqual(registry.get("transform", "x").run(), "second")

    def test_rejects_incompatible_contract(self):
        registry = PluginRegistry()
        d = PluginDescriptor("x", "transform", "1.0.0", 99)
        with self.assertRaises(ValueError):
            registry.register(d, self.Plugin("unused"))

    def test_allowlist_rejects_untrusted_modules(self):
        with tempfile.TemporaryDirectory() as td:
            manifest = Path(td) / "plugins.json"
            manifest.write_text(
                '{"contract_version": 1, "plugins": [{"id": "x", "kind": "transform", '
                '"version": "1.0.0", "contract_version": 1, "module": "os", '
                '"enabled": true}]}',
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                PluginRegistry().load_allowlist(manifest)


if __name__ == "__main__":
    unittest.main()
