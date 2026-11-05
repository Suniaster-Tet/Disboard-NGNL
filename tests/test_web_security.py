"""Pruebas de límites HTTP del dashboard."""
from __future__ import annotations

import base64

from fastapi.testclient import TestClient

from web.server import app


def _basic_auth(username: str, password: str) -> str:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return f"Basic {token}"


def test_remote_client_requires_credentials_and_https(monkeypatch):
    monkeypatch.setenv("DISBOARD_WEB_REQUIRE_AUTH", "false")
    monkeypatch.setenv("WEB_HOST", "127.0.0.1")
    monkeypatch.setenv("DISBOARD_WEB_AUTH_USERNAME", "tet")
    monkeypatch.setenv("DISBOARD_WEB_AUTH_PASSWORD", "a-long-test-password")
    monkeypatch.setenv("DISBOARD_WEB_TRUST_PROXY_HEADERS", "true")
    client = TestClient(app, client=("198.51.100.10", 1234))

    assert client.get("/api/status").status_code == 401
    auth = _basic_auth("tet", "a-long-test-password")
    assert client.get("/api/status", headers={"Authorization": auth}).status_code == 426
    response = client.get(
        "/api/status",
        headers={"Authorization": auth, "X-Forwarded-Proto": "https"},
    )
    assert response.status_code == 200


def test_remote_auth_fails_closed_for_missing_or_weak_credentials(monkeypatch):
    monkeypatch.setenv("DISBOARD_WEB_REQUIRE_AUTH", "true")
    monkeypatch.delenv("DISBOARD_WEB_AUTH_USERNAME", raising=False)
    monkeypatch.delenv("DISBOARD_WEB_AUTH_PASSWORD", raising=False)
    client = TestClient(app, client=("127.0.0.1", 8000))
    assert client.get("/api/status").status_code == 503

    monkeypatch.setenv("DISBOARD_WEB_AUTH_USERNAME", "tet")
    monkeypatch.setenv("DISBOARD_WEB_AUTH_PASSWORD", "short")
    assert client.get("/api/status").status_code == 503


def test_healthcheck_is_public_but_has_security_headers(monkeypatch):
    monkeypatch.setenv("DISBOARD_WEB_REQUIRE_AUTH", "true")
    client = TestClient(app, client=("198.51.100.10", 1234))
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["cache-control"] == "no-store"


def test_cross_origin_mutation_is_rejected(monkeypatch):
    monkeypatch.setenv("DISBOARD_WEB_REQUIRE_AUTH", "false")
    client = TestClient(app, client=("127.0.0.1", 8000))
    response = client.post(
        "/api/requests",
        json={"text": "No crear este edge."},
        headers={"Origin": "https://attacker.invalid"},
    )

    assert response.status_code == 403