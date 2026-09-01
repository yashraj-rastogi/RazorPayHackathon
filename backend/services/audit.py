"""
RevGuard — Append-only audit log writer.
Every write goes to Firestore's `audit_logs` collection.
No existing audit records are ever updated.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Any

from backend.models.audit import AuditLog, AuditAction, AuditActor
from backend.db.firestore import set_document, now_utc

logger = logging.getLogger(__name__)


def write_audit(
    action: AuditAction,
    actor: AuditActor = AuditActor.SYSTEM,
    stage: str = "system",
    case_id: Optional[str] = None,
    event_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> AuditLog:
    """
    Append one audit record. Never updates existing records.
    Returns the created AuditLog for inspection/chaining.
    """
    audit_id = f"audit_{uuid.uuid4().hex[:12]}"
    entry = AuditLog(
        audit_id=audit_id,
        case_id=case_id,
        event_id=event_id,
        timestamp=now_utc(),
        actor=actor,
        stage=stage,
        action=action,
        details=details or {},
    )

    try:
        set_document("audit_logs", audit_id, entry.model_dump(mode="json"))
    except Exception as exc:
        # Audit failure must never crash the main pipeline
        logger.error("Failed to write audit record %s: %s", audit_id, exc)

    return entry
