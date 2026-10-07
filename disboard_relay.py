"""Explicit artifact transfer client for an authenticated local Disboard host."""
import argparse
import hashlib
import hmac
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests

from disboard_artifacts import MAX_ARTIFACT_BYTES


def _configuration(url: str = "") -> tuple[str, str]:
    base_url = (url or os.environ.get("DISBOARD_RELAY_URL", "")).rstrip("/")
    token = os.environ.get("DISBOARD_RELAY_TOKEN", "")
    parsed = urlparse(base_url)
    if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("El relay requiere HTTPS (o loopback para pruebas locales).")
    if not parsed.netloc:
        raise ValueError("Define DISBOARD_RELAY_URL o proporciona --url.")
    if (
        parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise ValueError(
            "DISBOARD_RELAY_URL debe ser solo el origen HTTPS, sin credenciales ni ruta."
        )
    if len(token) < 32:
        raise ValueError("Define DISBOARD_RELAY_TOKEN con al menos 32 caracteres.")
    return base_url, token


def _raise_for_status(response: requests.Response) -> None:
    if 300 <= response.status_code < 400:
        response.close()
        raise requests.RequestException("El relay no admite redirecciones.")
    response.raise_for_status()


def upload_artifact(project: str, artifact_path: str, source_path: str, url: str = ""):
    base_url, token = _configuration(url)
    source = Path(source_path).expanduser()
    if source.is_symlink() or not source.is_file():
        raise ValueError("El archivo fuente debe existir y no ser enlace simbólico.")
    if source.stat().st_size > MAX_ARTIFACT_BYTES:
        raise ValueError(
            f"El archivo supera el límite de {MAX_ARTIFACT_BYTES} bytes."
        )
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    sha256 = digest.hexdigest()
    with source.open("rb") as stream:
        response = requests.post(
            f"{base_url}/api/relay/artifacts",
            headers={"Authorization": f"Bearer {token}"},
            data={"project": project, "path": artifact_path, "sha256": sha256},
            files={"file": (source.name, stream, "application/octet-stream")},
            timeout=(10, 180),
            allow_redirects=False,
        )
    _raise_for_status(response)
    result = response.json()
    if not hmac.compare_digest(result.get("sha256", ""), sha256):
        raise ValueError("El host reportó un SHA-256 distinto al archivo enviado.")
    return result


def download_artifact(project: str, artifact_path: str, destination_path: str, url: str = ""):
    base_url, token = _configuration(url)
    destination = Path(destination_path).expanduser()
    if destination.is_symlink() or destination.exists():
        raise FileExistsError("El destino existe o es un enlace simbólico; no se sobrescribe.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(
        f"{base_url}/api/relay/artifact",
        params={"project": project, "path": artifact_path},
        headers={"Authorization": f"Bearer {token}"},
        stream=True,
        timeout=(10, 180),
        allow_redirects=False,
    )
    _raise_for_status(response)
    expected_digest = response.headers.get("X-Disboard-Artifact-SHA256", "")
    if len(expected_digest) != 64:
        raise ValueError("El host no devolvió un SHA-256 válido.")
    digest = hashlib.sha256()
    size = 0
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".disboard-download-", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    size += len(chunk)
                    if size > MAX_ARTIFACT_BYTES:
                        raise ValueError(
                            f"La descarga supera el límite de {MAX_ARTIFACT_BYTES} bytes."
                        )
                    digest.update(chunk)
                    output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        if not hmac.compare_digest(digest.hexdigest(), expected_digest.casefold()):
            raise ValueError("El SHA-256 descargado no coincide con el del host.")
        os.link(temporary, destination)
        temporary.unlink()
        return {
            "project": project,
            "path": artifact_path,
            "destination": str(destination),
            "sha256": expected_digest,
        }
    finally:
        temporary.unlink(missing_ok=True)
        response.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="", help="URL HTTPS del host Tailscale Serve.")
    commands = parser.add_subparsers(dest="command", required=True)
    upload = commands.add_parser("upload", help="Copiar un archivo al almacén local.")
    upload.add_argument("project")
    upload.add_argument("artifact_path", help="Ruta relativa dentro del edge, por ejemplo docs/salida.md.")
    upload.add_argument("source")
    download = commands.add_parser("download", help="Descargar y verificar un artefacto.")
    download.add_argument("project")
    download.add_argument("artifact_path")
    download.add_argument("destination")
    listing = commands.add_parser("list", help="Listar los artefactos locales de un edge.")
    listing.add_argument("project")
    args = parser.parse_args()
    try:
        base_url, _ = _configuration(args.url)
        if args.command == "upload":
            result = upload_artifact(
                args.project, args.artifact_path, args.source, base_url
            )
            print(
                f"Guardado en host local: {result['project']}/{result['path']} "
                f"({result['sha256']})"
            )
        elif args.command == "download":
            result = download_artifact(
                args.project, args.artifact_path, args.destination, base_url
            )
            print(f"Descargado y verificado: {result['destination']} ({result['sha256']})")
        else:
            response = requests.get(
                f"{base_url}/api/relay/artifacts",
                params={"project": args.project},
                headers={"Authorization": f"Bearer {_configuration(args.url)[1]}"},
                timeout=(10, 30),
                allow_redirects=False,
            )
            _raise_for_status(response)
            for item in response.json()["artifacts"]:
                print(f"{item['sha256']}  {item['size']:>10}  {item['path']}")
    except (OSError, ValueError, requests.RequestException) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
