"""
Request-validation errors must be explainable from the server log and
readable in the client, and must never echo the submitted value back.

Background: 2026-10-19, a crawl submission got a bare 422 in production. The
log said only "Status: 422" and the SPA showed axios's "Request failed with
status code 422". See app/core/errors.py.
"""

import logging
import re
from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.errors import SERVER_ERROR_MESSAGE, describe, field_name, public_errors, summarize

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
def db_client():
    """Stand-in for the Supabase client; tests that need the DB to fail set
    side effects on it."""
    return MagicMock()


@pytest.fixture
def client(db_client):
    """Authenticated TestClient with the DB replaced by ``db_client``."""
    from app.core.auth import get_current_user
    from app.main import app
    from app.models.models import User
    from app.api.routes import crawls as crawls_route

    user = User(id=uuid4(), email="person@example.com", is_admin=True,
                created_at=datetime.now(), updated_at=datetime.now())
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        with patch.object(crawls_route, "get_auth_client", return_value=db_client):
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


# What Postgres said on 2026-10-20 when the API sent 1.0 to an INTEGER column.
PG_ERROR = "{'message': 'invalid input syntax for type integer: \"1.0\"', 'code': '22P02', 'hint': None, 'details': None}"


class TestServerErrors:
    """A 5xx never carries internals to the client; the log carries them
    under an id the client can quote."""

    def test_db_failure_is_a_calm_500_with_a_reference(self, client, db_client, caplog):
        db_client.table.return_value.insert.return_value.execute.side_effect = RuntimeError(PG_ERROR)
        with caplog.at_level(logging.ERROR, logger="app.core.errors"):
            r = client.post("/api/v1/crawls/", json=VALID_PAYLOAD)

        assert r.status_code == 500
        body = r.json()
        assert body["detail"] == SERVER_ERROR_MESSAGE
        assert re.fullmatch(r"[0-9a-f]{8}", body["error_id"])
        # Nothing from the driver reaches the client...
        assert "22P02" not in r.text
        assert "invalid input syntax" not in r.text
        # ...and the log ties the id to the cause.
        line = next(m for m in (rec.getMessage() for rec in caplog.records) if body["error_id"] in m)
        assert "POST /api/v1/crawls/" in line
        assert "22P02" in line

    def test_four_xx_messages_pass_through_untouched(self, client):
        # The user-agent rule raises a deliberate 422 with a sentence for people.
        r = client.post("/api/v1/crawls/", json={**VALID_PAYLOAD, "user_agent": "Mozilla/5.0 Chrome/120"})
        assert r.status_code == 422
        assert "error_id" not in r.json()
        assert r.json()["detail"] != SERVER_ERROR_MESSAGE

    def test_every_5xx_shares_the_shape(self, client, db_client):
        # The insert succeeds but the row cannot be fetched back: the route
        # raises its own HTTPException(500, "Crawl created but failed to retrieve.").
        fetch = db_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute
        fetch.return_value = MagicMock(error=MagicMock(message="boom"), data=None)
        r = client.post("/api/v1/crawls/", json=VALID_PAYLOAD)
        assert r.status_code == 500
        assert set(r.json()) == {"detail", "error_id"}
        assert "boom" not in r.text
