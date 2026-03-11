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

from app.db.supabase import supabase_client

logger = logging.getLogger(__name__)


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
        supabase_client.table("audit_log").insert(row).execute()
        logger.debug(f"Audit log: {action} on {entity_type}/{entity_id} by {user_id}")
    except Exception as e:
        # Audit logging should never break the main operation
        logger.error(f"Failed to write audit log: {e}")
