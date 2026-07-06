"""
Tests for Sentry event filtering (app/core/sentry_filtering.py).

These lock in the behavior that produced the 2026-06-30 noise incident: a
transient DNS/network failure must be recognized and dropped, while a real
application error must always pass through.
"""

import socket

from app.core.sentry_filtering import before_send, is_transient_network_error


# --- is_transient_network_error -------------------------------------------

def test_gaierror_is_transient():
    assert is_transient_network_error(socket.gaierror(-2, "Name or service not known"))


def test_oserror_dns_errnos_are_transient():
    assert is_transient_network_error(OSError(-2, "Name or service not known"))
    assert is_transient_network_error(OSError(-3, "Temporary failure in name resolution"))


def test_message_match_is_transient():
    # Wrappers (httpx/httpcore) often lose the original type but keep the text.
    assert is_transient_network_error(Exception("HTTPSConnectionPool: Max retries exceeded"))
    assert is_transient_network_error(RuntimeError("getaddrinfo failed"))


def test_transient_detected_through_exception_chain():
    """A wrapper whose __cause__ is a gaierror must still be recognized."""
    root = socket.gaierror(-3, "Temporary failure in name resolution")
    try:
        try:
            raise root
        except socket.gaierror as e:
            raise ValueError("could not connect to supabase") from e
    except ValueError as wrapper:
        assert is_transient_network_error(wrapper)


def test_real_error_is_not_transient():
    assert not is_transient_network_error(ValueError("column pages.word_count does not exist"))
    assert not is_transient_network_error(KeyError("user_id"))
    assert not is_transient_network_error(None)


# --- before_send -----------------------------------------------------------

def test_before_send_drops_transient():
    event = {"event_id": "abc"}
    hint = {"exc_info": (socket.gaierror, socket.gaierror(-2, "Name or service not known"), None)}
    assert before_send(event, hint) is None


def test_before_send_keeps_real_errors():
    event = {"event_id": "abc"}
    hint = {"exc_info": (ValueError, ValueError("real bug"), None)}
    assert before_send(event, hint) is event


def test_before_send_keeps_events_without_exc_info():
    """The loops' deliberate outage escalation logs a message with no
    exc_info — it must pass through so a sustained outage is still reported."""
    event = {"event_id": "abc", "message": "Storage cleanup has failed 3 consecutive times"}
    assert before_send(event, {}) is event
    assert before_send(event, None) is event
