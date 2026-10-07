#!/usr/bin/env python3
"""Private, local-first web interface for Disboard-NGNL."""
import argparse
import hmac
import json
import os
import re
import tempfile
import threading
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse
import requests

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DISBOARD_DATA_DIR", ROOT_DIR / ".disboard-local")).expanduser()
os.environ.setdefault("DISBOARD_DATA_DIR", str(DATA_DIR))

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from disboard_access import AccessRegistry, SESSION_SECONDS
from disboard_graph import DisboardAgentGraph
from disboard_usage import UsageLedger
from disboard_bibliography import BibliographyIngestor
from disboard_plugins import create_default_registry
from disboard_registry import project_by_slug, project_records, read_master_index


WEB_DIR = ROOT_DIR / "web"
registry = AccessRegistry(DATA_DIR / "access.sqlite3")
agent_graph = DisboardAgentGraph(ROOT_DIR)
usage_ledger = UsageLedger(DATA_DIR / "usage.sqlite3")
bibliography = BibliographyIngestor(ROOT_DIR)
plugin_registry = create_default_registry(ROOT_DIR)
run_lock = threading.BoundedSemaphore(1)
login_failures = {}
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/assets", StaticFiles(directory=WEB_DIR), name="assets")


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    access_key: str = Field(min_length=1, max_length=256)


class RunRequest(BaseModel):
    task: str = Field(min_length=1, max_length=12000)
    project: str = Field(default="", max_length=120)


class DOIRequest(BaseModel):
    project: str = Field(min_length=1, max_length=120)
    doi: str = Field(min_length=3, max_length=300)


def relay_storage(action, *args, **kwargs):
    storage_plugin = plugin_registry.get("storage", "local-filesystem")
    return storage_plugin.run(DATA_DIR / "artifacts", action, *args, **kwargs)


def require_active_project(project: str) -> dict[str, str]:
    try:
        index = read_master_index(ROOT_DIR / "Elkia.md")
    except (OSError, ValueError) as error:
        raise HTTPException(
            status_code=503, detail=f"No se pudo leer Elkia.md: {error}"
        ) from error
    record = project_by_slug(index, project)
    if not record:
        raise HTTPException(
            status_code=404, detail="El edge no está en el registro activo de Elkia.md."
        )
    if not re.fullmatch(r"edge-[A-Za-z0-9_-]+", record["slug"]):
        raise HTTPException(status_code=400, detail="El slug registrado no es válido.")
    project_path = (ROOT_DIR / record["slug"]).resolve()
    if project_path.parent != ROOT_DIR.resolve() or (ROOT_DIR / record["slug"]).is_symlink():
        raise HTTPException(status_code=400, detail="La ruta registrada sale del workspace.")
    return record


def _artifact_filename(filename: str) -> str:
    basename = (filename or "archivo").replace("\\", "/").rsplit("/", 1)[-1]
    basename = re.sub(r"[^A-Za-z0-9_.-]+", "_", basename).lstrip(".")
    if not basename or basename in {".", ".."}:
        basename = f"archivo-{uuid.uuid4().hex}"
    return basename[:180]


def require_relay_token(request: Request):
    expected = os.environ.get("DISBOARD_RELAY_TOKEN", "")
    if len(expected) < 32:
        raise HTTPException(
            status_code=503,
            detail="El relay está deshabilitado: configura un token de al menos 32 caracteres.",
        )
    authorization = request.headers.get("authorization", "")
    supplied = authorization.removeprefix("Bearer ").strip()
    if not hmac.compare_digest(expected, supplied):
        raise HTTPException(status_code=401, detail="Credencial de relay inválida.")


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; "
        "img-src 'self' data:; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
    )
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response


def require_same_origin(request):
    origin = request.headers.get("origin")
    if origin and urlparse(origin).netloc != request.url.netloc:
        raise HTTPException(status_code=403, detail="Origen no autorizado.")


def current_user(request: Request):
    username = registry.session_user(request.cookies.get("disboard_session"))
    if not username:
        raise HTTPException(status_code=401, detail="Inicia sesión para continuar.")
    return username


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/status")
def status():
    return {
        "registered_users": len(registry.list_users()),
        "local_model_configured": bool(os.environ.get("DISBOARD_OLLAMA_MODEL")),
        "public_doi_lookup_enabled": os.environ.get("DISBOARD_ALLOW_PUBLIC_DOI_LOOKUP") == "1",
        "inference_mode": "local-only",
    }


@app.get("/api/session")
def session(username=Depends(current_user)):
    return {"username": username}


@app.get("/api/artifacts")
def local_artifact_list(project: str, username=Depends(current_user)):
    require_active_project(project)
    try:
        records = relay_storage("list", project)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {
        "project": project,
        "artifacts": [
            {"path": record.path, "size": record.size, "sha256": record.sha256}
            for record in records
        ],
    }


@app.post("/api/artifacts")
def local_artifact_upload(
    request: Request,
    project: str = Form(...),
    file: UploadFile = File(...),
    username=Depends(current_user),
):
    require_same_origin(request)
    require_active_project(project)
    artifact_path = (
        f"uploads/{time.time_ns()}-{_artifact_filename(file.filename or '')}"
    )
    try:
        record = relay_storage("put", project, artifact_path, file.file)
    except (ValueError, OSError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    finally:
        file.file.close()
    return {
        "project": record.project,
        "path": record.path,
        "size": record.size,
        "sha256": record.sha256,
    }


@app.get("/api/artifacts/download")
def local_artifact_download(
    project: str, path: str, username=Depends(current_user)
):
    require_active_project(project)
    try:
        record = relay_storage("inspect", project, path)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return FileResponse(
        record.stored_path,
        filename=Path(record.path).name,
        media_type="application/octet-stream",
        headers={"X-Disboard-Artifact-SHA256": record.sha256},
    )


@app.get("/api/relay/artifacts")
def relay_list(project: str, request: Request):
    require_relay_token(request)
    require_active_project(project)
    try:
        records = relay_storage("list", project)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {
        "project": project,
        "artifacts": [
            {"path": record.path, "size": record.size, "sha256": record.sha256}
            for record in records
        ],
    }


@app.post("/api/relay/artifacts")
def relay_upload(
    request: Request,
    project: str = Form(...),
    path: str = Form(...),
    sha256: str = Form(...),
    file: UploadFile = File(...),
):
    require_same_origin(request)
    require_relay_token(request)
    require_active_project(project)
    try:
        record = relay_storage(
            "put", project, path, file.file, expected_sha256=sha256
        )
    except FileExistsError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except (ValueError, OSError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    finally:
        file.file.close()
    return {
        "project": record.project,
        "path": record.path,
        "size": record.size,
        "sha256": record.sha256,
    }


@app.get("/api/relay/artifact")
def relay_download(project: str, path: str, request: Request):
    require_relay_token(request)
    require_active_project(project)
    try:
        record = relay_storage("inspect", project, path)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return FileResponse(
        record.stored_path,
        filename=Path(record.path).name,
        media_type="application/octet-stream",
        headers={"X-Disboard-Artifact-SHA256": record.sha256},
    )


@app.get("/api/usage")
def usage(agent: str = "", username=Depends(current_user)):
    config_path = ROOT_DIR / "exeed_config.json"
    config = __import__("json").loads(config_path.read_text(encoding="utf-8"))
    known_agents = config.get("agent_models", {})
    if agent and agent.lower() not in known_agents:
        raise HTTPException(status_code=404, detail="Agente no encontrado en la configuración.")
    return {
        "window_hours": 24,
        "agent": agent or "all",
        "agents": sorted(known_agents),
        "limits": config.get("usage_limits", {}),
        "usage": usage_ledger.summary(agent=agent, hours=24),
        "balance_source": "Límites configurables; los proveedores no exponen un saldo común verificable.",
    }


@app.post("/api/bibliography/doi")
def bibliography_doi(payload: DOIRequest, request: Request, username=Depends(current_user)):
    require_same_origin(request)
    require_active_project(payload.project)
    try:
        output = bibliography.ingest(payload.project, doi=payload.doi)
    except (ValueError, FileNotFoundError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except requests.RequestException as error:
        raise HTTPException(status_code=502, detail=f"Falló la consulta pública de metadatos: {error}") from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return {"source": output, "metadata_lookup_enabled": os.environ.get("DISBOARD_ALLOW_PUBLIC_DOI_LOOKUP") == "1"}


@app.post("/api/bibliography/pdf")
def bibliography_pdf(
    request: Request,
    project: str = Form(...),
    file: UploadFile = File(...),
    username=Depends(current_user),
):
    require_same_origin(request)
    require_active_project(project)
    if Path(file.filename or "").suffix.lower() != ".pdf":
        raise HTTPException(status_code=415, detail="Selecciona un archivo PDF.")
    contents = file.file.read(30 * 1024 * 1024 + 1)
    if len(contents) > 30 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="El PDF supera el límite de 30 MB.")
    if not contents.startswith(b"%PDF-"):
        raise HTTPException(status_code=415, detail="El archivo no tiene una cabecera PDF válida.")
    temporary_dir = DATA_DIR / "incoming"
    temporary_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary_path = tempfile.mkstemp(suffix=".pdf", dir=temporary_dir)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(contents)
        output = bibliography.ingest(project, pdf_path=temporary_path)
    except (ValueError, FileNotFoundError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except (requests.RequestException, LookupError) as error:
        raise HTTPException(
            status_code=502,
            detail=f"Falló la consulta pública de citaciones: {error}",
        ) from error
    finally:
        Path(temporary_path).unlink(missing_ok=True)
        file.file.close()
    return {"source": output, "metadata_lookup_enabled": os.environ.get("DISBOARD_ALLOW_PUBLIC_DOI_LOOKUP") == "1"}


@app.get("/api/bibliography")
def bibliography_notes(project: str, username=Depends(current_user)):
    require_active_project(project)
    if not project.startswith("edge-") or "/" in project or "\\" in project:
        raise HTTPException(status_code=400, detail="Proyecto no válido.")
    project_dir = (ROOT_DIR / project).resolve()
    if project_dir.parent != ROOT_DIR:
        raise HTTPException(status_code=400, detail="Proyecto fuera del workspace.")
    notes_dir = project_dir / "docs" / "bibliografia"
    notes = []
    proposals = []
    if notes_dir.is_dir() and not notes_dir.is_symlink():
        active_dois = set()
        for note in sorted(notes_dir.glob("*.md"))[:30]:
            if note.is_symlink() or not note.is_file():
                continue
            markdown = note.read_text(encoding="utf-8")[:40000]
            active_dois.update(
                (match.group(1) or match.group(2)).casefold()
                for match in re.finditer(
                    r"^\- \*\*DOI:\*\* (?:`([^`]+)`|([^\s]+))$",
                    markdown,
                    re.MULTILINE,
                )
            )
            notes.append({
                "path": note.relative_to(project_dir).as_posix(),
                "markdown": markdown,
            })
        proposals_dir = notes_dir / "propuestas"
        if proposals_dir.is_dir() and not proposals_dir.is_symlink():
            candidates_by_doi = {}
            candidates_dir = proposals_dir / "candidatos"
            if candidates_dir.is_dir() and not candidates_dir.is_symlink():
                for candidate_file in sorted(candidates_dir.glob("*.json")):
                    if candidate_file.is_symlink() or not candidate_file.is_file():
                        continue
                    candidate = json.loads(candidate_file.read_text(encoding="utf-8"))
                    candidate_doi = str(candidate.get("doi", ""))
                    if candidate_doi:
                        candidates_by_doi[candidate_doi.casefold()] = candidate_doi
            for proposal in sorted(proposals_dir.glob("*.md"))[:30]:
                if proposal.is_symlink() or not proposal.is_file():
                    continue
                markdown = proposal.read_text(encoding="utf-8")[:40000]
                referenced_dois = {
                    match.group(1).casefold()
                    for match in re.finditer(
                        r"^\- \*\*DOI:\*\* `([^`]+)`$", markdown, re.MULTILINE
                    )
                }
                candidate_dois = [
                    doi for doi_key, doi in candidates_by_doi.items()
                    if doi_key in referenced_dois and doi_key not in active_dois
                ]
                proposals.append({
                    "path": proposal.relative_to(project_dir).as_posix(),
                    "markdown": markdown,
                    "pending_dois": candidate_dois,
                })
    return {"notes": notes, "proposals": proposals}


@app.post("/api/bibliography/approve")
def bibliography_approve(
    payload: DOIRequest,
    request: Request,
    username=Depends(current_user),
):
    require_same_origin(request)
    require_active_project(payload.project)
    if username.casefold() != "tet":
        raise HTTPException(
            status_code=403,
            detail="Solo Tet puede aprobar la incorporación de referencias.",
        )
    try:
        output = bibliography.approve_citation(
            payload.project, payload.doi, approved_by=username
        )
    except (ValueError, FileNotFoundError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileExistsError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {"source": output, "approved_by": username}


@app.post("/api/login")
def login(payload: LoginRequest, request: Request, response: Response):
    require_same_origin(request)
    now = time.time()
    address = request.client.host if request.client else "unknown"
    recent_failures = [stamp for stamp in login_failures.get(address, []) if now - stamp < 300]
    if len(recent_failures) >= 5:
        raise HTTPException(status_code=429, detail="Demasiados intentos. Espera cinco minutos.")

    username = registry.authenticate(payload.username, payload.access_key)
    if not username:
        recent_failures.append(now)
        login_failures[address] = recent_failures
        raise HTTPException(status_code=401, detail="Credenciales no válidas.")

    login_failures.pop(address, None)
    token = registry.create_session(username)
    response.set_cookie(
        "disboard_session",
        token,
        max_age=SESSION_SECONDS,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="strict",
        path="/",
    )
    return {"username": username}


@app.post("/api/logout")
def logout(request: Request, response: Response, username=Depends(current_user)):
    require_same_origin(request)
    registry.revoke_session(request.cookies.get("disboard_session"))
    response.delete_cookie("disboard_session", path="/", httponly=True, samesite="strict")
    return {"ok": True}


@app.get("/api/projects")
def projects(username=Depends(current_user)):
    index = read_master_index(ROOT_DIR / "Elkia.md")
    found = []
    for record in project_records(index):
        slug = record["slug"]
        if not re.fullmatch(r"edge-[A-Za-z0-9_-]+", slug):
            continue
        path = (ROOT_DIR / slug).resolve()
        if (
            path.parent != ROOT_DIR.resolve()
            or (ROOT_DIR / slug).is_symlink()
            or not path.is_dir()
            or not (path / "contract.md").is_file()
        ):
            continue
        found.append({
            "slug": slug,
            "name": f"{record['id']} — {record['title']}",
        })
    return {"projects": found}


@app.post("/api/runs")
def run_agents(payload: RunRequest, request: Request, username=Depends(current_user)):
    require_same_origin(request)
    task = payload.task.strip()
    if not task:
        raise HTTPException(status_code=422, detail="Escribe una tarea antes de iniciar.")
    project = payload.project.strip()
    if project:
        if not project_by_slug(read_master_index(ROOT_DIR / "Elkia.md"), project):
            raise HTTPException(
                status_code=404, detail="El edge no está en el registro activo de Elkia.md."
            )
        project_path = (ROOT_DIR / project).resolve()
        if project_path.parent != ROOT_DIR or not project_path.name.startswith("edge-"):
            raise HTTPException(status_code=400, detail="Proyecto no permitido.")
        if not (project_path / "contract.md").is_file():
            raise HTTPException(status_code=404, detail="No se encontró el contrato del proyecto.")
    if not os.environ.get("DISBOARD_OLLAMA_MODEL"):
        raise HTTPException(
            status_code=503,
            detail="Modo privado activo. Configura DISBOARD_OLLAMA_MODEL con un modelo local instalado.",
        )
    if not run_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Ya hay una ejecución local en curso.")
    try:
        try:
            return agent_graph.run(task, project)
        except RuntimeError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=f"Falló el flujo local: {error}") from error
    finally:
        run_lock.release()


def main():
    parser = argparse.ArgumentParser(description="Iniciar la interfaz local de Disboard.")
    parser.add_argument("--host", default="127.0.0.1", help="Por defecto solo loopback.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--tls-certfile")
    parser.add_argument("--tls-keyfile")
    args = parser.parse_args()
    is_loopback = args.host in {"127.0.0.1", "localhost", "::1"}
    if not is_loopback and not (args.tls_certfile and args.tls_keyfile):
        parser.error("Para escuchar en la LAN debes proporcionar certificado y llave TLS.")
    if bool(args.tls_certfile) != bool(args.tls_keyfile):
        parser.error("Debes proporcionar juntos --tls-certfile y --tls-keyfile.")
    if args.tls_keyfile and Path(args.tls_keyfile).stat().st_mode & 0o077:
        parser.error("La llave TLS debe tener permisos solo para su propietario (chmod 600).")

    import uvicorn

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        ssl_certfile=args.tls_certfile,
        ssl_keyfile=args.tls_keyfile,
        server_header=False,
    )


if __name__ == "__main__":
    main()