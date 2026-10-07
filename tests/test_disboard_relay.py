import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from disboard_relay import _configuration, download_artifact, upload_artifact
from disboard_registry import (
    REGISTRY_END,
    REGISTRY_START,
    register_project,
    render_project_table,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def create_empty_elkia(path):
    content = (REPOSITORY_ROOT / "Elkia.md").read_text(encoding="utf-8")
    start = content.index(REGISTRY_START) + len(REGISTRY_START)
    end = content.index(REGISTRY_END, start)
    content = content[:start] + "\n" + render_project_table([]) + "\n" + content[end:]
    path.write_text(content, encoding="utf-8")


class RelayClientTests(unittest.TestCase):
    TOKEN = "relay-token-for-test-with-at-least-32-characters"

    def test_requires_https_outside_loopback_and_a_long_token(self):
        with patch.dict(
            "os.environ",
            {"DISBOARD_RELAY_URL": "http://host.example", "DISBOARD_RELAY_TOKEN": self.TOKEN},
        ):
            with self.assertRaisesRegex(ValueError, "requiere HTTPS"):
                _configuration()
        with patch.dict(
            "os.environ",
            {"DISBOARD_RELAY_URL": "https://host.example", "DISBOARD_RELAY_TOKEN": "short"},
        ):
            with self.assertRaisesRegex(ValueError, "al menos 32"):
                _configuration()
        with patch.dict(
            "os.environ",
            {
                "DISBOARD_RELAY_URL": "https://user:secret@host.example",
                "DISBOARD_RELAY_TOKEN": self.TOKEN,
            },
        ):
            with self.assertRaisesRegex(ValueError, "sin credenciales"):
                _configuration()

    @patch("disboard_relay.requests.post")
    def test_upload_sends_hash_and_checks_local_host_acknowledgement(self, post):
        content = b"cloud result"
        digest = hashlib.sha256(content).hexdigest()

        class Response:
            status_code = 200

            @staticmethod
            def raise_for_status():
                return None

            @staticmethod
            def json():
                return {"sha256": digest, "project": "edge-test", "path": "results.md"}

        post.return_value = Response()
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "result.md"
            source.write_bytes(content)
            with patch.dict(
                "os.environ",
                {
                    "DISBOARD_RELAY_URL": "https://laptop.tailnet.ts.net",
                    "DISBOARD_RELAY_TOKEN": self.TOKEN,
                },
            ):
                result = upload_artifact("edge-test", "results.md", str(source))

        self.assertEqual(result["sha256"], digest)
        self.assertEqual(post.call_args.kwargs["data"]["sha256"], digest)
        self.assertFalse(post.call_args.kwargs["allow_redirects"])

    @patch("disboard_relay.requests.post")
    def test_upload_rejects_a_local_file_larger_than_the_relay_limit(self, post):
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "large.bin"
            with source.open("wb") as stream:
                stream.truncate(50 * 1024 * 1024 + 1)
            with patch.dict(
                "os.environ",
                {
                    "DISBOARD_RELAY_URL": "https://laptop.tailnet.ts.net",
                    "DISBOARD_RELAY_TOKEN": self.TOKEN,
                },
            ):
                with self.assertRaisesRegex(ValueError, "supera el límite"):
                    upload_artifact("edge-test", "large.bin", str(source))
        post.assert_not_called()

    @patch("disboard_relay.requests.get")
    def test_download_verifies_hash_before_creating_destination(self, get):
        content = b"local artifact"
        digest = hashlib.sha256(content).hexdigest()

        class Response:
            status_code = 200
            headers = {"X-Disboard-Artifact-SHA256": digest}

            @staticmethod
            def raise_for_status():
                return None

            @staticmethod
            def iter_content(chunk_size):
                yield content

            @staticmethod
            def close():
                return None

        get.return_value = Response()
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "result.md"
            with patch.dict(
                "os.environ",
                {
                    "DISBOARD_RELAY_URL": "https://laptop.tailnet.ts.net",
                    "DISBOARD_RELAY_TOKEN": self.TOKEN,
                },
            ):
                result = download_artifact(
                    "edge-test", "result.md", str(destination)
                )
            self.assertEqual(destination.read_bytes(), content)
            self.assertEqual(result["sha256"], digest)

    @patch("disboard_relay.requests.get")
    def test_download_rejects_tampering_and_never_overwrites_existing_file(self, get):
        class Response:
            status_code = 200
            headers = {"X-Disboard-Artifact-SHA256": "0" * 64}

            @staticmethod
            def raise_for_status():
                return None

            @staticmethod
            def iter_content(chunk_size):
                yield b"tampered"

            @staticmethod
            def close():
                return None

        get.return_value = Response()
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "result.md"
            with patch.dict(
                "os.environ",
                {
                    "DISBOARD_RELAY_URL": "https://laptop.tailnet.ts.net",
                    "DISBOARD_RELAY_TOKEN": self.TOKEN,
                },
            ):
                with self.assertRaisesRegex(ValueError, "no coincide"):
                    download_artifact("edge-test", "result.md", str(destination))
            self.assertFalse(destination.exists())
            destination.write_text("keep", encoding="utf-8")
            with patch.dict(
                "os.environ",
                {
                    "DISBOARD_RELAY_URL": "https://laptop.tailnet.ts.net",
                    "DISBOARD_RELAY_TOKEN": self.TOKEN,
                },
            ):
                with self.assertRaises(FileExistsError):
                    download_artifact("edge-test", "result.md", str(destination))


class RelayApiTests(unittest.TestCase):
    TOKEN = "relay-token-for-api-test-with-at-least-32-chars"

    def test_api_authenticates_and_round_trips_private_artifacts(self):
        from fastapi.testclient import TestClient

        with tempfile.TemporaryDirectory() as temporary_directory:
            data_dir = Path(temporary_directory)
            create_empty_elkia(data_dir / "Elkia.md")
            register_project(
                data_dir / "Elkia.md", "API", "edge-api", "API test edge"
            )
            (data_dir / "edge-api").mkdir()
            (data_dir / "edge-api" / "contract.md").write_text(
                "# API test\n", encoding="utf-8"
            )
            with patch.dict(
                "os.environ",
                {
                    "DISBOARD_DATA_DIR": str(data_dir),
                    "DISBOARD_RELAY_TOKEN": self.TOKEN,
                },
            ):
                import disboard_web

                with (
                    patch.object(disboard_web, "ROOT_DIR", data_dir),
                    patch.object(disboard_web, "DATA_DIR", data_dir / "private"),
                    TestClient(disboard_web.app) as client,
                ):
                    unauthorized = client.get(
                        "/api/relay/artifacts", params={"project": "edge-api"}
                    )
                    self.assertEqual(unauthorized.status_code, 401)

                    content = b"local API report"
                    digest = hashlib.sha256(content).hexdigest()
                    upload = client.post(
                        "/api/relay/artifacts",
                        headers={"Authorization": f"Bearer {self.TOKEN}"},
                        data={
                            "project": "edge-api",
                            "path": "results/report.md",
                            "sha256": digest,
                        },
                        files={"file": ("report.md", content, "text/markdown")},
                    )
                    self.assertEqual(upload.status_code, 200, upload.text)
                    self.assertEqual(upload.json()["sha256"], digest)

                    listing = client.get(
                        "/api/relay/artifacts",
                        headers={"Authorization": f"Bearer {self.TOKEN}"},
                        params={"project": "edge-api"},
                    )
                    self.assertEqual(
                        [item["path"] for item in listing.json()["artifacts"]],
                        ["results/report.md"],
                    )

                    download = client.get(
                        "/api/relay/artifact",
                        headers={"Authorization": f"Bearer {self.TOKEN}"},
                        params={"project": "edge-api", "path": "results/report.md"},
                    )
                    self.assertEqual(download.content, content)
                    self.assertEqual(
                        download.headers["x-disboard-artifact-sha256"], digest
                    )


if __name__ == "__main__":
    unittest.main()
