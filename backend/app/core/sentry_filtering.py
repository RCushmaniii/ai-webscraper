"""
Sentry event filtering to keep the error stream signal-rich.

Transient network / DNS failures (Supabase or an upstream site briefly
unreachable, a VPS name-resolution hiccup) are infrastructure blips, not
application bugs. Left unfiltered they flood Sentry: a single outage on
2026-06-30 produced 850+ events from the background-task loops alone, all
variants of "Name or service not known". We drop those here so that what
reaches Sentry is actionable.

A *sustained* outage is still surfaced, but deliberately and once: the
background loops (see app/main.py) escalate to a single plain-text
``logger.error`` after N consecutive transient failures. That escalation
carries no exception ``exc_info``, so it passes this filter untouched.
"""

import logging
import socket
from typing import Optional

logger = logging.getLogger(__name__)

# errno values Linux getaddrinfo returns when DNS resolution fails:
#   -2 = EAI_NONAME ("Name or service not known")
#   -3 = EAI_AGAIN  ("Temporary failure in name resolution")
_TRANSIENT_ERRNOS = {-2, -3}

# Lowercased substrings that identify a transient network/DNS failure by
# message, covering wrappers (httpx -> httpcore -> socket) that don't always
# preserve the original exception type.
_TRANSIENT_MESSAGES = (
    "name or service not known",
    "temporary failure in name resolution",
    "getaddrinfo failed",
    "name resolution",
    "connection reset by peer",
    "connection aborted",
    "max retries exceeded",
)


def is_transient_network_error(exc: Optional[BaseException]) -> bool:
    """
    Return True if ``exc`` — or anything in its cause/context chain — is a
    transient network/DNS failure rather than an application bug.

    Walks ``__cause__``/``__context__`` because the SDK usually surfaces the
    outermost wrapper (e.g. an httpx error) while the DNS ``gaierror`` sits
    several links down the chain.
    """
    seen: set[int] = set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))

        if isinstance(exc, socket.gaierror):
            return True
        if isinstance(exc, OSError) and exc.errno in _TRANSIENT_ERRNOS:
            return True

        msg = str(exc).lower()
        if any(marker in msg for marker in _TRANSIENT_MESSAGES):
            return True

        exc = exc.__cause__ or exc.__context__

    return False


def before_send(event, hint):
    """
    Sentry ``before_send`` hook: drop transient network/DNS noise.

    Returning ``None`` discards the event. Only events whose captured
    exception is a transient network error are dropped; everything else
    (real application errors, and the loops' deliberate outage escalation,
    which has no ``exc_info``) passes through unchanged.
    """
    exc_info = hint.get("exc_info") if hint else None
    if exc_info:
        exc = exc_info[1]
        if is_transient_network_error(exc):
            return None
    return event
