import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from disboard_artifacts import LocalArtifactStore
from disboard_plugins import (
    CONTRACT_VERSION,
    PluginDescriptor,
    PluginRegistry,
    create_default_registry,
)


class PluginRegistryTests(unittest.TestCase):
    class Plugin:
        def __init__(self, value):
            self.value = value

        def run(self, *args, **kwargs):
            return self.value

    def test_default_plugins_are_explicit_and_contract_versioned(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            registry = create_default_registry()
            plugin = registry.get("storage", "local-filesystem")

            self.assertEqual(
                plugin.run(
                    Path(temporary_directory) / "artifacts",
                    "list",
                    "edge-empty",
                ),
                [],
            )
            self.assertEqual(registry.list()[0].contract_version, CONTRACT_VERSION)

    def test_replacement_requires_explicit_opt_in(self):
        registry = PluginRegistry()
        descriptor = PluginDescriptor("example.block", "transform", "1.0.0", 1)
        registry.register(descriptor, self.Plugin("first"))

        with self.assertRaisesRegex(ValueError, "ya está registrado"):
            registry.register(descriptor, self.Plugin("replacement"))
        registry.register(
            descriptor, self.Plugin("replacement"), replace_existing=True
        )

        self.assertEqual(registry.get("transform", "example.block").run(), "replacement")

    def test_rejects_incompatible_contracts(self):
        registry = PluginRegistry()
        descriptor = PluginDescriptor("example.block", "transform", "1.0.0", 99)

        with self.assertRaisesRegex(ValueError, "Contrato incompatible"):
            registry.register(descriptor, self.Plugin("unused"))

    def test_allowlist_refuses_untrusted_module_prefixes_before_import(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            manifest = Path(temporary_directory) / "plugins.json"
            manifest.write_text(
                json.dumps({
                    "contract_version": 1,
                    "plugins": [{
                        "id": "custom.transform",
                        "kind": "transform",
                        "version": "1.0.0",
                        "contract_version": 1,
                        "module": "os",
                        "enabled": True,
                    }],
                }),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Solo se permiten módulos"):
                PluginRegistry().load_allowlist(manifest)

    def test_allowlisted_extension_can_replace_a_block_by_contract(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            manifest = Path(temporary_directory) / "plugins.json"
            manifest.write_text(
                json.dumps({
                    "contract_version": 1,
                    "plugins": [{
                        "id": "local-filesystem",
                        "kind": "storage",
                        "version": "1.0.1",
                        "contract_version": 1,
                        "module": "disboard_ext.local_artifact_store",
                        "factory": "create_plugin",
                        "enabled": True,
                        "replace": True,
                    }],
                }),
                encoding="utf-8",
            )
            registry = create_default_registry()
            registry.load_allowlist(manifest)
            plugin = registry.get("storage", "local-filesystem")

            self.assertEqual(
                plugin.run(
                    Path(temporary_directory) / "artifacts",
                    "list",
                    "edge-empty",
                ),
                [],
            )


class LocalArtifactStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.store = LocalArtifactStore(self.root / "artifacts", max_bytes=64)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_stores_hashes_lists_and_reads_artifacts(self):
        content = b"# local result\n"
        digest = hashlib.sha256(content).hexdigest()
        record = self.store.put(
            "edge-results", "docs/report.md", io.BytesIO(content), digest
        )

        self.assertEqual(record.sha256, digest)
        self.assertEqual(self.store.inspect("edge-results", "docs/report.md"), record)
        self.assertEqual(
            [item.path for item in self.store.list("edge-results")],
            ["docs/report.md"],
        )
        verified, stream = self.store.open_verified("edge-results", "docs/report.md")
        with stream:
            self.assertEqual(stream.read(), content)
        self.assertEqual(verified.sha256, digest)

    def test_rejects_traversal_mismatched_hash_and_overwrite(self):
        with self.assertRaisesRegex(ValueError, "relativa y segura"):
            self.store.put("edge-data", "../secret", io.BytesIO(b"x"))
        with self.assertRaisesRegex(ValueError, "no coincide"):
            self.store.put("edge-data", "docs/out.md", io.BytesIO(b"content"), "0" * 64)

        content = b"result"
        digest = hashlib.sha256(content).hexdigest()
        self.store.put("edge-data", "docs/out.md", io.BytesIO(content), digest)
        with self.assertRaises(FileExistsError):
            self.store.put("edge-data", "docs/out.md", io.BytesIO(b"other"))

    def test_detects_local_tampering_and_rejects_oversized_uploads(self):
        digest = hashlib.sha256(b"ok").hexdigest()
        record = self.store.put("edge-data", "docs/out.md", io.BytesIO(b"ok"), digest)
        record.stored_path.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "no coincide"):
            self.store.inspect("edge-data", "docs/out.md")

        with self.assertRaisesRegex(ValueError, "supera el límite"):
            self.store.put("edge-data", "docs/large.bin", io.BytesIO(b"x" * 65))


if __name__ == "__main__":
    unittest.main()
