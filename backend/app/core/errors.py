"""
Uniform, safe error responses: request validation (422) and server errors (5xx).

Why this exists (2026-10-19): a crawl submission was rejected with a 422 in
production and nobody could tell why. FastAPI's default handler returns a raw
list of Pydantic error objects and logs nothing, so the server log showed only
"Status: 422" and the SPA, finding no string to display, fell back to axios's
"Request failed with status code 422". A user-facing product must never show
that, and an operator must never be blind to why a request was refused.

The default body also echoes ``input`` (whatever the client sent) back in the
response. For a form that is harmless; for a header or token it replays
secrets into screenshots and logs. We strip it.

Then, 2026-10-20: the next failure was a 500 whose toast read
"An unexpected error occurred: {'message': 'invalid input syntax for type
integer: "1.0"', 'code': '22P02', ...}". Every route wraps its body in
``except Exception as e: raise HTTPException(500, detail=f"...: {e}")``, so
whatever a driver, Postgres or an upstream API said went straight to the
screen. That is useless to the person and a free map of the internals to
anyone else. Server errors now leave with one calm sentence and a short
reference id; the real cause is logged under that id.

Contract (kept stable for the SPA, see frontend/src/lib/apiError.ts):

    422 {"detail": [{"loc": [...], "msg": "...", "type": "..."}, ...],
         "message": "url: URL must start with http:// or https://"}

    5xx {"detail": "Something went wrong on our side. ...",
         "error_id": "3f9a1c2e"}

``detail`` on a 422 keeps FastAPI's shape minus ``input``/``ctx``/``url``;
``message`` is a one-line human summary built from field name + reason.
4xx HTTPExceptions are deliberate messages written for people and pass
through unchanged.
"""

import logging
import secrets
from typing import Any, Iterable, Optional, Sequence

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler as _default_http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

# First element of a Pydantic ``loc`` is where the value came from; it is
# noise in a message meant for a person ("body.url" -> "url").
_LOCATION_PREFIXES = frozenset({"body", "query", "path", "header", "cookie"})

# Pydantic prefixes messages raised by custom validators with this.
_VALUE_ERROR_PREFIX = "Value error, "

# The only sentence a 5xx body ever carries. Mirrored verbatim in the SPA so
# the user sees the same words whether the body was readable or not.
SERVER_ERROR_MESSAGE = "Something went wrong on our side. It has been logged; please try again in a moment."


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


def new_error_id() -> str:
    """Eight hex characters: short enough to read off a toast, random enough
    to be unique in a log search."""
    return secrets.token_hex(4)


def server_error_response(
    request: Request,
    cause: str,
    *,
    status_code: int = 500,
    headers: Optional[dict] = None,
    exc_info: Any = None,
) -> JSONResponse:
    """The one way a 5xx leaves this app.

    ``cause`` is what the operator needs (the driver/Postgres/upstream text);
    it goes to the log under ``error_id`` and never into the body. The
    status code is preserved because 502/503/504 carry meaning for proxies
    and clients; the words are replaced.
    """
    error_id = new_error_id()
    logger.error(
        "Server error %s on %s %s (status %d): %s",
        error_id, request.method, request.url.path, status_code, cause,
        exc_info=exc_info,
    )
    return JSONResponse(
        status_code=status_code,
        content={"detail": SERVER_ERROR_MESSAGE, "error_id": error_id},
        headers=headers,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """4xx: the route wrote a sentence for the user; keep it. 5xx: sanitize."""
    if exc.status_code >= 500:
        return server_error_response(
            request, str(exc.detail), status_code=exc.status_code, headers=exc.headers
        )
    return await _default_http_exception_handler(request, exc)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Anything a route did not catch. The request-logging middleware in
    main.py normally sees these first and calls server_error_response itself;
    this handler keeps the contract if that middleware is ever removed."""
    return server_error_response(request, repr(exc), exc_info=exc)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
