"""Smoke test del dashboard real con Playwright."""
from __future__ import annotations

import re
import socket
import threading
import time
from pathlib import Path

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

pytestmark = pytest.mark.slow


def test_dashboard_browser_smoke(tmp_path, monkeypatch) -> None:
    with sync_playwright() as playwright:
        browser_types = (playwright.chromium, playwright.firefox, playwright.webkit)
        installed = [
            browser_type
            for browser_type in browser_types
            if Path(browser_type.executable_path).exists()
        ]
        if not installed:
            pytest.skip("Playwright instalado sin navegadores; ejecuta `playwright install`.")

        monkeypatch.setenv(
            "DISBOARD_WEB_CHECKPOINT_DB", str(tmp_path / "web_checkpoints.sqlite")
        )
        import web.server as web_server
        from elkia.registry import ElkiaRegistry

        edges_root = tmp_path / "edges"
        monkeypatch.setattr("core.edge.EDGES_ROOT", edges_root)
        registry = ElkiaRegistry(ruta=edges_root / "elkia_registry.json")
        monkeypatch.setattr(web_server, "ElkiaRegistry", lambda: registry)
        monkeypatch.setattr("web.dashboard.views.ElkiaRegistry", lambda: registry)

        import uvicorn

        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            port = listener.getsockname()[1]
            server = uvicorn.Server(uvicorn.Config(web_server.app, log_level="error"))
            thread = threading.Thread(
                target=server.run,
                kwargs={"sockets": [listener]},
                daemon=True,
            )
            thread.start()
            deadline = time.monotonic() + 10
            while not server.started and thread.is_alive() and time.monotonic() < deadline:
                threading.Event().wait(0.01)
            if not server.started:
                server.should_exit = True
                thread.join(timeout=5)
                raise RuntimeError("FastAPI no inició para el smoke test.")

            try:
                for browser_type in installed:
                    try:
                        browser = browser_type.launch()
                    except PlaywrightError as error:
                        if "error while loading shared libraries" in str(error):
                            pytest.skip(
                                "Faltan bibliotecas del sistema para Chromium; "
                                "reconstruye el devcontainer o instala Playwright con --with-deps."
                            )
                        raise
                    try:
                        page = browser.new_page(viewport={"width": 1280, "height": 900})
                        page_errors: list[str] = []
                        page.on("pageerror", lambda error: page_errors.append(str(error)))
                        page.goto(f"http://127.0.0.1:{port}/", wait_until="networkidle")
                        page.get_by_role("heading", name="Disboard-NGNL").wait_for()
                        page.get_by_role("link", name="Nuevo edge").click()
                        page.locator('input[name="title"]').fill("Browser smoke edge")
                        page.locator('textarea[name="seed"]').fill(
                            "Probar la creación de un edge desde el navegador."
                        )
                        page.get_by_role("button", name="Crear y proponer plan").click()
                        page.wait_for_url(re.compile(r"/edges/edge-browser-smoke-edge-[a-f0-9]+$"))
                        page.get_by_text("Browser smoke edge").wait_for()
                        page.get_by_role("heading", name="Plan de Sora").wait_for()

                        page.set_viewport_size({"width": 390, "height": 844})
                        dimensions = page.evaluate(
                            "() => ({viewport: document.documentElement.clientWidth, "
                            "content: document.documentElement.scrollWidth})"
                        )
                        if dimensions["content"] > dimensions["viewport"] + 1:
                            raise AssertionError(f"Desbordamiento móvil: {dimensions}")
                        if page_errors:
                            raise AssertionError("; ".join(page_errors))
                    finally:
                        browser.close()
            finally:
                server.should_exit = True
                thread.join(timeout=5)
