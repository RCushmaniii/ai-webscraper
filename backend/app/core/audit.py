"""
Audit logging utility for admin actions.

Logs important actions (user management, crawl creation/deletion) to the
audit_log table for accountability and debugging. Uses the service-role
client to bypass RLS so audit entries are always written regardless of
the acting user's permissions.

IMPORTANT: Audit logging must NEVER break the main operation. All calls
are wrapped in try/except and failures are logged but swallowed.
"""

import logging
from typing import Optional
from uuid import UUID

from supabase import create_client, Client

from app.core.config import settings

logger = logging.getLogger(__name__)

# The shared app.db.supabase singleton is built with the ANON key, so its
# inserts are subject to RLS — which is why audit writes were failing with
# "new row violates row-level security policy for table audit_log" (42501).
# Audit logging must bypass RLS, so use a dedicated service-role client
# (same pattern as worker.py / storage.py). Lazily created so importing this
# module never requires the service key to be present (e.g. in tests).
_service_client: Optional[Client] = None


def _get_service_client() -> Client:
    global _service_client
    if _service_client is None:
        _service_client = create_client(
            settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY
        )
    return _service_client


def log_audit_event(
    user_id: str,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> None:
    """
    Log an admin/user action to the audit_log table.

    Uses the service-role client so inserts always succeed regardless of RLS.

    Args:
        user_id: UUID of the user performing the action.
        action: Short verb describing the action (e.g. "create_crawl", "delete_user").
        entity_type: Type of entity acted upon (e.g. "crawl", "user").
        entity_id: Optional ID of the target entity.
        details: Optional dict of extra context (stored as JSONB).
        ip_address: Optional client IP address.
    """
    try:
        row = {
            "user_id": str(user_id),
            "action": action,
            "entity_type": entity_type,
            "entity_id": str(entity_id) if entity_id else None,
            "details": details or {},
        }
        if ip_address:
            row["ip_address"] = ip_address

        # Use service-role client to bypass RLS
        _get_service_client().table("audit_log").insert(row).execute()
        logger.debug(f"Audit log: {action} on {entity_type}/{entity_id} by {user_id}")
    except Exception as e:
        # Audit logging should never break the main operation
        logger.error(f"Failed to write audit log: {e}")
