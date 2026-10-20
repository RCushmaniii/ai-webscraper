"""
Uniform, safe error responses for request validation failures.

Why this exists (2026-10-19): a crawl submission was rejected with a 422 in
production and nobody could tell why. FastAPI's default handler returns a raw
list of Pydantic error objects and logs nothing, so the server log showed only
"Status: 422" and the SPA, finding no string to display, fell back to axios's
"Request failed with status code 422". A user-facing product must never show
that, and an operator must never be blind to why a request was refused.

The default body also echoes ``input`` (whatever the client sent) back in the
response. For a form that is harmless; for a header or token it replays
secrets into screenshots and logs. We strip it.

Contract (kept stable for the SPA, see frontend/src/lib/apiError.ts):

    422 {"detail": [{"loc": [...], "msg": "...", "type": "..."}, ...],
         "message": "url: URL must start with http:// or https://"}

``detail`` keeps FastAPI's shape minus ``input``/``ctx``/``url``; ``message``
is a one-line human summary built from field name + reason.
"""

import logging
from typing import Any, Iterable, Sequence

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# First element of a Pydantic ``loc`` is where the value came from; it is
# noise in a message meant for a person ("body.url" -> "url").
_LOCATION_PREFIXES = frozenset({"body", "query", "path", "header", "cookie"})

# Pydantic prefixes messages raised by custom validators with this.
_VALUE_ERROR_PREFIX = "Value error, "


def field_name(loc: Sequence[Any]) -> str:
    """``("body", "url")`` -> ``"url"``; ``("body",)`` -> ``"body"``."""
    parts = [str(p) for p in loc]
    if len(parts) > 1 and parts[0] in _LOCATION_PREFIXES:
        rest = parts[1:]
        # A purely numeric remainder is a byte offset into a raw body (JSON
        # decode errors report ("body", 30)); "30: JSON decode error" helps nobody.
        if all(p.isdigit() for p in rest):
            return parts[0]
        parts = rest
    return ".".join(parts) or "request"


def describe(error: dict) -> str:
    """One validation error as ``field: reason``."""
    msg = str(error.get("msg") or "Invalid value")
    if msg.startswith(_VALUE_ERROR_PREFIX):
        msg = msg[len(_VALUE_ERROR_PREFIX):]
    return f"{field_name(error.get('loc', ()))}: {msg}"


def summarize(errors: Iterable[dict]) -> str:
    return "; ".join(describe(e) for e in errors) or "Request could not be validated"


def public_errors(errors: Iterable[dict]) -> list:
    """The error list with only the keys a client needs. Never ``input``."""
    return [
        {
            "loc": [str(p) for p in e.get("loc", ())],
            "msg": str(e.get("msg") or "Invalid value"),
            "type": str(e.get("type") or "value_error"),
        }
        for e in errors
    ]


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    summary = summarize(errors)
    # WARNING, not ERROR: a rejected request is the API working as designed,
    # but an operator reading the log must be able to see the reason without
    # asking the user for a screenshot. Values are deliberately not logged.
    logger.warning("Validation rejected %s %s: %s", request.method, request.url.path, summary)
    return JSONResponse(
        status_code=422,
        content={"detail": public_errors(errors), "message": summary},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
