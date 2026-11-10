"""Web UI smoke tests — health, security headers, validation, localhost-only (4.0.1).

httpx's ASGI transport is async-only, so each request is driven with
asyncio.run(). The transport's client address is 127.0.0.1, so requests
pass the localhost-only middleware; a raw ASGI call with a non-loopback
client address verifies the 403 path.
"""
import asyncio

import httpx

from web.app import create_app

APP = create_app()
BASE_URL = "http://127.0.0.1:8000"


def _request(method, path, **kwargs):
    async def _go():
        transport = httpx.ASGITransport(app=APP)
        async with httpx.AsyncClient(
            transport=transport, base_url=BASE_URL
        ) as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(_go())


def test_health_endpoint():
    resp = _request("GET", "/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "4.0.2"


def test_security_headers_present():
    resp = _request("GET", "/health")
    assert "Content-Security-Policy" in resp.headers
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["X-Content-Type-Options"] == "nosniff"


def test_index_serves_ui():
    resp = _request("GET", "/")
    assert resp.status_code == 200
    assert "Pentia" in resp.text


def test_recon_rejects_malicious_target():
    # Argument-injection attempt must be a 400, never a scan.
    resp = _request("POST", "/api/recon", json={"target": "; rm -rf /", "fast": True})
    assert resp.status_code == 400


def test_recon_rejects_leading_dash_target():
    resp = _request(
        "POST", "/api/recon", json={"target": "-oN /tmp/out", "fast": True}
    )
    assert resp.status_code == 400


def test_chat_rejects_flag_like_model():
    resp = _request(
        "POST", "/api/chat", json={"message": "hola", "model": "--insecure"}
    )
    assert resp.status_code == 400


def test_non_loopback_client_is_forbidden():
    """Raw ASGI call with a non-loopback peer must get 403."""
    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/health",
        "raw_path": b"/health",
        "query_string": b"",
        "headers": [],
        "client": ("203.0.113.1", 1234),
        "server": ("127.0.0.1", 8000),
    }
    asyncio.run(APP(scope, receive, send))
    assert messages, "app sent no ASGI messages"
    assert messages[0]["type"] == "http.response.start"
    assert messages[0]["status"] == 403
