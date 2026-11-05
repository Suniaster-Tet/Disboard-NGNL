"""Controles HTTP defensivos del dashboard."""
from __future__ import annotations

import base64
import binascii
import hmac
import os
from urllib.parse import urlsplit

from fastapi import Request
from fastapi.responses import PlainTextResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware


def _enabled(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _loopback(host: str) -> bool:
    return host.strip("[]").lower() in {"127.0.0.1", "::1", "localhost"}


class DashboardSecurityMiddleware(BaseHTTPMiddleware):
    """Exige autenticación en despliegues remotos y valida mutaciones de origen."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path == "/healthz":
            response = await call_next(request)
            return self._secure_headers(response, request)

        client_host = request.client.host if request.client else ""
        local_client = _loopback(client_host)
        auth_required = _enabled(os.getenv("DISBOARD_WEB_REQUIRE_AUTH")) or not local_client
        if auth_required:
            username = os.getenv("DISBOARD_WEB_AUTH_USERNAME", "")
            password = os.getenv("DISBOARD_WEB_AUTH_PASSWORD", "")
            if not username or len(password) < 12 or ":" in username:
                response = PlainTextResponse(
                    "El dashboard requiere usuario y contraseña de al menos 12 caracteres.",
                    status_code=503,
                )
                return self._secure_headers(response, request)
            supplied = self._basic_credentials(request.headers.get("authorization", ""))
            if not supplied or not (
                hmac.compare_digest(supplied[0], username)
                and hmac.compare_digest(supplied[1], password)
            ):
                response = PlainTextResponse(
                    "Autenticación requerida.",
                    status_code=401,
                    headers={"WWW-Authenticate": 'Basic realm="Disboard-NGNL", charset="UTF-8"'},
                )
                return self._secure_headers(response, request)

            if not local_client:
                scheme = request.url.scheme.lower()
                if _enabled(os.getenv("DISBOARD_WEB_TRUST_PROXY_HEADERS")):
                    scheme = request.headers.get("x-forwarded-proto", scheme).split(",", 1)[0].strip().lower()
                if scheme != "https":
                    response = PlainTextResponse(
                        "El acceso remoto requiere HTTPS.", status_code=426
                    )
                    return self._secure_headers(response, request)

        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            fetch_site = request.headers.get("sec-fetch-site", "").lower()
            host = request.headers.get("host", "").lower()
            allowed = {
                item.strip().rstrip("/").lower()
                for item in os.getenv("DISBOARD_WEB_ALLOWED_ORIGINS", "").split(",")
                if item.strip()
            }
            try:
                origin_host = urlsplit(origin).netloc.lower() if origin else ""
            except ValueError:
                origin_host = ""
            if fetch_site == "cross-site" or (
                origin and origin_host != host and origin.rstrip("/").lower() not in allowed
            ):
                response = PlainTextResponse("Origen no permitido.", status_code=403)
                return self._secure_headers(response, request)

        response = await call_next(request)
        return self._secure_headers(response, request)

    @staticmethod
    def _basic_credentials(header: str) -> tuple[str, str] | None:
        scheme, _, encoded = header.partition(" ")
        if scheme.lower() != "basic" or not encoded:
            return None
        try:
            decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError, ValueError):
            return None
        username, separator, password = decoded.partition(":")
        return (username, password) if separator else None

    @staticmethod
    def _secure_headers(response: Response, request: Request) -> Response:
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
            "connect-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'",
        )
        scheme = request.url.scheme.lower()
        if _enabled(os.getenv("DISBOARD_WEB_TRUST_PROXY_HEADERS")):
            scheme = request.headers.get("x-forwarded-proto", scheme).split(",", 1)[0].strip().lower()
        if scheme == "https":
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response