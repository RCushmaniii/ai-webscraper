"""
Request-validation errors must be explainable from the server log and
readable in the client, and must never echo the submitted value back.

Background: 2026-10-19, a crawl submission got a bare 422 in production. The
log said only "Status: 422" and the SPA showed axios's "Request failed with
status code 422". See app/core/errors.py.
"""

import logging
from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.errors import describe, field_name, public_errors, summarize

VALID_PAYLOAD = {
    "url": "https://www.example.com",
    "name": "Example",
    "max_depth": 2,
    "max_pages": 10,
    "respect_robots_txt": True,
    "follow_external_links": False,
    "js_rendering": False,
    "rate_limit": 1,
}


@pytest.fixture
def client():
    """Authenticated TestClient; the DB is never reached because every test
    here is rejected at validation, before the route body runs."""
    from app.core.auth import get_current_user
    from app.main import app
    from app.models.models import User
    from app.api.routes import crawls as crawls_route

    user = User(id=uuid4(), email="person@example.com", is_admin=True,
                created_at=datetime.now(), updated_at=datetime.now())
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        with patch.object(crawls_route, "get_auth_client", return_value=MagicMock()):
            with TestClient(app, raise_server_exceptions=False) as c:
                yield c
    finally:
        app.dependency_overrides.pop(get_current_user, None)


class TestHelpers:
    def test_field_name_drops_location_prefix(self):
        assert field_name(("body", "url")) == "url"
        assert field_name(("query", "page")) == "page"
        assert field_name(("body", "items", 0, "name")) == "items.0.name"

    def test_field_name_keeps_bare_body(self):
        # A missing body altogether is reported at loc ("body",)
        assert field_name(("body",)) == "body"
        assert field_name(()) == "request"

    def test_field_name_hides_byte_offsets(self):
        # Malformed JSON is reported at ("body", <offset>)
        assert field_name(("body", 30)) == "body"

    def test_describe_strips_pydantic_value_error_prefix(self):
        err = {"loc": ("body", "url"), "msg": "Value error, URL must start with http:// or https://"}
        assert describe(err) == "url: URL must start with http:// or https://"

    def test_summarize_joins_errors(self):
        errors = [
            {"loc": ("body", "url"), "msg": "Field required"},
            {"loc": ("body", "rate_limit"), "msg": "Input should be greater than or equal to 0.1"},
        ]
        assert summarize(errors) == (
            "url: Field required; rate_limit: Input should be greater than or equal to 0.1"
        )
        assert summarize([]) == "Request could not be validated"

    def test_public_errors_never_carry_input(self):
        errors = [{"loc": ("body", "url"), "msg": "x", "type": "t", "input": "SECRET", "ctx": {"e": ValueError("x")}}]
        out = public_errors(errors)
        assert out == [{"loc": ["body", "url"], "msg": "x", "type": "t"}]


class TestCreateCrawlValidation:
    def test_bad_url_scheme_is_explained(self, client, caplog):
        payload = {**VALID_PAYLOAD, "url": "ftp://sekrit-host.example"}
        with caplog.at_level(logging.WARNING, logger="app.core.errors"):
            r = client.post("/api/v1/crawls/", json=payload)

        assert r.status_code == 422
        body = r.json()
        assert body["message"] == "url: URL must start with http:// or https://"
        assert body["detail"][0]["loc"] == ["body", "url"]
        # The submitted value is never echoed back to the client...
        assert "sekrit-host" not in r.text
        # ...and the operator can see why from the log alone, also without the value.
        assert any(
            "Validation rejected POST /api/v1/crawls/: url: URL must start with http:// or https://" in rec.getMessage()
            for rec in caplog.records
        )
        assert "sekrit-host" not in caplog.text

    def test_out_of_range_number_names_the_field(self, client):
        r = client.post("/api/v1/crawls/", json={**VALID_PAYLOAD, "rate_limit": 0})
        assert r.status_code == 422
        assert r.json()["message"].startswith("rate_limit: ")

    def test_several_errors_are_all_listed(self, client):
        r = client.post("/api/v1/crawls/", json={**VALID_PAYLOAD, "max_depth": 99, "max_pages": 0})
        assert r.status_code == 422
        message = r.json()["message"]
        assert "max_depth: " in message
        assert "max_pages: " in message
        assert len(r.json()["detail"]) == 2

    def test_malformed_json_is_a_422_with_a_message(self, client):
        r = client.post(
            "/api/v1/crawls/",
            content=b'{"url": "https://example.com",',
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 422
        assert r.json()["message"].startswith("body")

    def test_missing_body_is_a_422_with_a_message(self, client):
        r = client.post("/api/v1/crawls/", content=b"", headers={"Content-Type": "application/json"})
        assert r.status_code == 422
        assert r.json()["message"] == "body: Field required"

    def test_valid_payload_is_not_touched_by_the_handler(self, client):
        # Not a full happy path (DB mocked away); the point is that the handler
        # only fires on validation failures.
        r = client.post("/api/v1/crawls/", json=VALID_PAYLOAD)
        assert r.status_code != 422
