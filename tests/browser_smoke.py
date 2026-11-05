"""Cross-engine UI smoke test with a static server and mocked local API.

Marcado como slow: requiere que el dashboard web exista y que Playwright esté
instalado. Se salta automáticamente si `web/templates/index.html` no existe.
"""
from __future__ import annotations

import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WEB_INDEX = ROOT / "web" / "templates" / "index.html"

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not WEB_INDEX.exists(), reason="dashboard web aún no implementado"),
]


class DisboardStaticHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        if urlsplit(path).path.startswith("/assets/"):
            path = "/web/" + urlsplit(path).path.removeprefix("/assets/")
        return super().translate_path(path)


def api_response(route) -> None:
    request = route.request
    path = request.url.split("?", 1)[0]
    if path.endswith("/api/status"):
        payload = {"registered_users": 1, "local_model_configured": True,
                   "public_doi_lookup_enabled": False, "inference_mode": "local-only"}
    elif path.endswith("/api/session"):
        payload = {"username": "Tet"}
    elif path.endswith("/api/projects"):
        payload = {"projects": [{"slug": "edge-smoke", "name": "SMOKE — Browser test"}]}
    elif path.endswith("/api/usage"):
        payload = {"agents": [], "limits": {}, "usage": []}
    elif path.endswith("/api/bibliography"):
        payload = {"notes": [], "proposals": []}
    elif path.endswith("/api/artifacts") and request.method == "POST":
        payload = {"project": "edge-smoke", "path": "uploads/smoke.txt",
                   "size": 18, "sha256": "a" * 64}
    elif path.endswith("/api/artifacts"):
        payload = {"project": "edge-smoke", "artifacts": []}
    elif path.endswith("/api/runs"):
        payload = {"plan": "Plan smoke", "draft": "Borrador smoke",
                   "review": "Revisión smoke", "approved_by_agent": False,
                   "revisions": 1, "trace": []}
    else:
        payload = {}
    route.fulfill(status=200, content_type="application/json",
                  body=json.dumps(payload, ensure_ascii=False))


def check_browser(browser_type, base_url: str) -> None:
    browser = browser_type.launch()
    try:
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page_errors: list[str] = []
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.route("**/api/**", api_response)
        page.goto(base_url, wait_until="networkidle")
        page.locator("#workspace-view:not([hidden])").wait_for()
        page.locator("#project-select").select_option("edge-smoke")

        page.get_by_role("tab", name="Archivos").click()
        page.locator("#artifact-input").set_input_files({
            "name": "smoke.txt", "mimeType": "text/plain",
            "buffer": b"browser smoke test"})
        page.get_by_role("button", name="Guardar en el host").click()

        page.get_by_role("tab", name="Chat").click()
        page.locator("#task-input").fill("Probar la interfaz entre motores.")
        page.get_by_role("button", name="Enviar").click()
        if page_errors:
            raise AssertionError("; ".join(page_errors))

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(100)
        dims = page.evaluate(
            "() => ({viewport: document.documentElement.clientWidth, "
            "content: document.documentElement.scrollWidth})")
        if dims["content"] > dims["viewport"] + 1:
            raise AssertionError(f"Horizontal overflow at mobile viewport: {dims}")
        print(f"{browser_type.name}: PASS (desktop and 390px viewport)")
    finally:
        browser.close()


def test_cross_engine_ui_smoke() -> None:
    handler = partial(DisboardStaticHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}/web/templates/"
    try:
        with sync_playwright() as playwright:
            for browser_type in (playwright.chromium, playwright.firefox, playwright.webkit):
                check_browser(browser_type, base_url)
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
