"""
HTTP-level smoke tests for the FastAPI app.

The unit suite covers crawler, issue detector and models; nothing exercised the
wired application until 2026-10-18 — a broken import in a router, a middleware
that swallowed auth, or a renamed health payload would all have shipped green.
These tests boot the real `app` (Supabase/config mocked by conftest) and assert
the contract the production smoke test (scripts/smoke-prod.sh) relies on.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from app.main import app

    # raise_server_exceptions=False so a 500 is observed as a response, not a
    # test crash — that is what a real client would see.
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestHealth:
    def test_api_health_reports_version(self, client):
        r = client.get("/api/v1/health/")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["version"] == "test-sha"
        assert body["environment"] == "development"

    def test_root_health_alias(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"
        assert r.json()["version"] == "test-sha"

    def test_openapi_schema_is_served(self, client):
        r = client.get("/api/v1/openapi.json")
        assert r.status_code == 200
        paths = r.json()["paths"]
        assert "/api/v1/health/" in paths
        assert "/api/v1/crawls/" in paths


class TestSecurityHeaders:
    def test_hardening_headers_present(self, client):
        r = client.get("/api/v1/health/")
        assert r.headers["X-Content-Type-Options"] == "nosniff"
        assert r.headers["X-Frame-Options"] == "DENY"
        assert r.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "camera=()" in r.headers["Permissions-Policy"]
        assert "X-Process-Time" in r.headers

    def test_hsts_only_off_localhost(self, client):
        local = client.get("/api/v1/health/", headers={"host": "localhost:8000"})
        assert "Strict-Transport-Security" not in local.headers
        prod = client.get("/api/v1/health/", headers={"host": "scraper.cushlabs.ai"})
        assert prod.headers["Strict-Transport-Security"].startswith("max-age=31536000")

    def test_oversized_body_rejected(self, client):
        r = client.post(
            "/api/v1/crawls/",
            headers={"content-length": str(11 * 1024 * 1024), "content-type": "application/json"},
        )
        assert r.status_code == 413


class TestAuthGate:
    """Every data endpoint must refuse anonymous callers before touching the DB."""

    @pytest.mark.parametrize(
        "method,path",
        [
            ("GET", "/api/v1/crawls/"),
            ("GET", "/api/v1/crawls/usage"),
            ("GET", "/api/v1/users/me"),
            ("GET", "/api/v1/users/"),
            ("POST", "/api/v1/crawls/"),
        ],
    )
    def test_anonymous_is_rejected(self, client, method, path):
        r = client.request(method, path, json={} if method == "POST" else None)
        # HTTPBearer returns 403 when the header is missing, 401 when invalid.
        assert r.status_code in (401, 403), f"{method} {path} -> {r.status_code}"

    def test_garbage_bearer_token_is_rejected(self, client):
        r = client.get("/api/v1/crawls/", headers={"Authorization": "Bearer not-a-jwt"})
        assert r.status_code == 401


class TestCors:
    def test_allowed_origin_preflight(self, client):
        r = client.options(
            "/api/v1/crawls/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        assert r.status_code == 200
        assert r.headers["access-control-allow-origin"] == "http://localhost:3000"

    def test_unknown_origin_gets_no_cors_grant(self, client):
        r = client.get("/api/v1/health/", headers={"Origin": "https://evil.example"})
        assert "access-control-allow-origin" not in r.headers
