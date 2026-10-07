"""Local, content-verified artifact storage for Disboard edges."""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import BinaryIO


PROJECT_SLUG = re.compile(r"^edge-[A-Za-z0-9_-]+$")
MAX_ARTIFACT_BYTES = 50 * 1024 * 1024


@dataclass(frozen=True)
class ArtifactRecord:
    project: str
    path: str
    size: int
    sha256: str
    stored_path: Path


class LocalArtifactStore:
    """Store artifacts below one private root; project/path never escape that root."""

    def __init__(self, root: str | Path, max_bytes: int = MAX_ARTIFACT_BYTES):
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if os.name == "posix":
            self.root.chmod(0o700)
        self.max_bytes = max_bytes

    def _target(self, project: str, artifact_path: str) -> tuple[Path, str]:
        if not PROJECT_SLUG.fullmatch(project):
            raise ValueError("El identificador debe ser un proyecto edge válido.")
        relative = PurePosixPath(artifact_path)
        if (
            not artifact_path
            or relative.is_absolute()
            or "\\" in artifact_path
            or any(part in {"", ".", ".."} for part in relative.parts)
            or any(part.startswith(".upload-") or part.endswith(".sha256") for part in relative.parts)
        ):
            raise ValueError("La ruta del artefacto debe ser relativa y segura.")
        target_parts = (project, *relative.parts)
        parent_parts = target_parts[:-1]
        parent = self.root
        for part in parent_parts:
            parent = parent / part
            if parent.is_symlink():
                raise ValueError(
                    "No se permiten enlaces simbólicos en la ruta del artefacto."
                )
            try:
                parent.mkdir(mode=0o700)
            except FileExistsError:
                if not parent.is_dir():
                    raise
            if not parent.resolve().is_relative_to(self.root):
                raise ValueError("La ruta del artefacto sale del almacenamiento local.")
        target = self.root.joinpath(*target_parts)
        if target.is_symlink():
            raise ValueError("No se permiten enlaces simbólicos en la ruta del artefacto.")
        resolved = target.resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as error:
            raise ValueError("La ruta del artefacto sale del almacenamiento local.") from error
        return resolved, relative.as_posix()

    def put(
        self,
        project: str,
        artifact_path: str,
        source: BinaryIO,
        expected_sha256: str = "",
    ) -> ArtifactRecord:
        target, normalized_path = self._target(project, artifact_path)
        if target.exists():
            existing = self.inspect(project, normalized_path)
            if expected_sha256 and existing.sha256 == expected_sha256.casefold():
                return existing
            raise FileExistsError(f"El artefacto ya existe: {project}/{normalized_path}")

        digest = hashlib.sha256()
        size = 0
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".upload-", dir=target.parent
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as output:
                while chunk := source.read(1024 * 1024):
                    size += len(chunk)
                    if size > self.max_bytes:
                        raise ValueError(
                            f"El artefacto supera el límite de {self.max_bytes} bytes."
                        )
                    digest.update(chunk)
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
            sha256 = digest.hexdigest()
            if expected_sha256 and not hmac.compare_digest(
                sha256, expected_sha256.casefold()
            ):
                raise ValueError("El SHA-256 recibido no coincide con el archivo.")
            try:
                os.link(temporary_path, target)
            except FileExistsError as error:
                raise FileExistsError(
                    f"El artefacto ya existe: {project}/{normalized_path}"
                ) from error
            temporary_path.unlink()
            checksum_path = target.with_name(target.name + ".sha256")
            if checksum_path.exists() or checksum_path.is_symlink():
                target.unlink(missing_ok=True)
                raise FileExistsError(
                    f"El hash del artefacto ya existe: {project}/{normalized_path}"
                )
            checksum_descriptor, checksum_temporary_name = tempfile.mkstemp(
                prefix=".upload-", dir=target.parent
            )
            checksum_temporary = Path(checksum_temporary_name)
            try:
                with os.fdopen(checksum_descriptor, "w", encoding="ascii") as sidecar:
                    sidecar.write(sha256 + "\n")
                    sidecar.flush()
                    os.fsync(sidecar.fileno())
                os.link(checksum_temporary, checksum_path)
            except OSError:
                target.unlink(missing_ok=True)
                raise
            finally:
                checksum_temporary.unlink(missing_ok=True)
            if os.name == "posix":
                target.chmod(0o600)
                checksum_path.chmod(0o600)
            return ArtifactRecord(project, normalized_path, size, sha256, target)
        finally:
            temporary_path.unlink(missing_ok=True)

    def inspect(self, project: str, artifact_path: str) -> ArtifactRecord:
        target, normalized_path = self._target(project, artifact_path)
        if not target.is_file() or target.is_symlink():
            raise FileNotFoundError(f"No existe el artefacto: {project}/{normalized_path}")
        digest = hashlib.sha256()
        size = 0
        with target.open("rb") as source:
            while chunk := source.read(1024 * 1024):
                digest.update(chunk)
                size += len(chunk)
        sha256 = digest.hexdigest()
        checksum_path = target.with_name(target.name + ".sha256")
        if not checksum_path.is_file():
            raise ValueError(f"Falta el hash registrado para {project}/{normalized_path}.")
        recorded_sha256 = checksum_path.read_text(encoding="ascii").strip()
        if not hmac.compare_digest(sha256, recorded_sha256):
            raise ValueError(f"El hash local no coincide para {project}/{normalized_path}.")
        return ArtifactRecord(project, normalized_path, size, sha256, target)

    def open_verified(self, project: str, artifact_path: str) -> tuple[ArtifactRecord, BinaryIO]:
        record = self.inspect(project, artifact_path)
        return record, record.stored_path.open("rb")

    def list(self, project: str) -> list[ArtifactRecord]:
        if not PROJECT_SLUG.fullmatch(project):
            raise ValueError("El identificador debe ser un proyecto edge válido.")
        project_dir = self.root / project
        if not project_dir.exists():
            return []
        if project_dir.is_symlink():
            raise ValueError("El directorio del proyecto no puede ser un enlace simbólico.")
        records = []
        for path in sorted(project_dir.rglob("*")):
            if path.is_symlink():
                raise ValueError("El almacenamiento contiene un enlace simbólico.")
            if path.is_file():
                if path.name.endswith(".sha256"):
                    continue
                relative = path.relative_to(project_dir).as_posix()
                records.append(self.inspect(project, relative))
        return records
