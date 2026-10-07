"""Cross-engine UI smoke test with a static server and mocked local API."""
from __future__ import annotations

import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]


class DisboardStaticHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        if urlsplit(path).path.startswith("/assets/"):
            path = "/web/" + urlsplit(path).path.removeprefix("/assets/")
        return super().translate_path(path)


def api_response(route) -> None:
    request = route.request
    path = request.url.split("?", 1)[0]
    if path.endswith("/api/status"):
        payload = {
            "registered_users": 1,
            "local_model_configured": True,
            "public_doi_lookup_enabled": False,
            "inference_mode": "local-only",
        }
    elif path.endswith("/api/session"):
        payload = {"username": "Tet"}
    elif path.endswith("/api/projects"):
        payload = {"projects": [{"slug": "edge-smoke", "name": "SMOKE — Browser test"}]}
    elif path.endswith("/api/usage"):
        payload = {"agents": [], "limits": {}, "usage": []}
    elif path.endswith("/api/bibliography"):
        payload = {"notes": [], "proposals": []}
    elif path.endswith("/api/artifacts") and request.method == "POST":
        payload = {
            "project": "edge-smoke",
            "path": "uploads/smoke.txt",
            "size": 18,
            "sha256": "a" * 64,
        }
    elif path.endswith("/api/artifacts"):
        payload = {"project": "edge-smoke", "artifacts": []}
    elif path.endswith("/api/runs"):
        payload = {
            "plan": "Plan smoke",
            "draft": "Borrador smoke",
            "review": "Revisión smoke",
            "approved_by_agent": False,
            "revisions": 1,
            "trace": [
                {"agent": "Sora", "stage": "Plan", "status": "Completado"},
                {"agent": "Shiro", "stage": "Ejecución", "status": "Completado"},
            ],
        }
    else:
        payload = {}
    route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps(payload, ensure_ascii=False),
    )


def check_browser(browser_type, base_url: str) -> None:
    browser = browser_type.launch()
    try:
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page_errors = []
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.route("**/api/**", api_response)
        page.goto(base_url, wait_until="networkidle")
        page.locator("#workspace-view:not([hidden])").wait_for()
        page.locator("#project-select").select_option("edge-smoke")

        page.get_by_role("tab", name="Archivos").click()
        page.get_by_text("Este proyecto aún no tiene archivos en el almacén local.").wait_for()
        page.locator("#artifact-input").set_input_files({
            "name": "smoke.txt",
            "mimeType": "text/plain",
            "buffer": b"browser smoke test",
        })
        page.get_by_role("button", name="Guardar en el host").click()
        page.get_by_text("Guardado en el host como uploads/smoke.txt").wait_for()

        page.get_by_role("tab", name="Bibliografía").click()
        page.get_by_text("Este proyecto aún no tiene notas bibliográficas.").wait_for()
        page.get_by_role("tab", name="Chat").click()
        page.locator("#task-input").fill("Probar la interfaz entre motores.")
        page.get_by_role("button", name="Enviar").click()
        page.get_by_text("Borrador smoke").wait_for()
        if page_errors:
            raise AssertionError("; ".join(page_errors))

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(100)
        dimensions = page.evaluate(
            "() => ({viewport: document.documentElement.clientWidth, "
            "content: document.documentElement.scrollWidth})"
        )
        if dimensions["content"] > dimensions["viewport"] + 1:
            raise AssertionError(f"Horizontal overflow at mobile viewport: {dimensions}")
        print(f"{browser_type.name}: PASS (desktop and 390px viewport)")
    finally:
        browser.close()


def main() -> None:
    handler = partial(DisboardStaticHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}/web/"
    try:
        with sync_playwright() as playwright:
            for browser_type in (
                playwright.chromium,
                playwright.firefox,
                playwright.webkit,
            ):
                check_browser(browser_type, base_url)
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


if __name__ == "__main__":
    main()
