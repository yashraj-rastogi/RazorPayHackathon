"""
RevGuard — Audit log Pydantic model and action enum.
Audit records are ALWAYS append-only. Never update existing records.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class AuditAction(str, Enum):
    # Ingestion
    EVENT_RECEIVED = "EVENT_RECEIVED"
    DUPLICATE_EVENT_BLOCKED = "DUPLICATE_EVENT_BLOCKED"

    # Diagnosis
    DIAGNOSIS_COMPLETED = "DIAGNOSIS_COMPLETED"
    AI_DIAGNOSIS_REQUESTED = "AI_DIAGNOSIS_REQUESTED"
    AI_DIAGNOSIS_FAILED = "AI_DIAGNOSIS_FAILED"
    AI_DIAGNOSIS_FALLBACK = "AI_DIAGNOSIS_FALLBACK"

    # Policy
    DECISION_MADE = "DECISION_MADE"

    # Recovery
    ACTION_CREATED = "ACTION_CREATED"
    ACTION_EXECUTED = "ACTION_EXECUTED"
    ACTION_FAILED = "ACTION_FAILED"
    ACTION_UNKNOWN = "ACTION_UNKNOWN"
    ACTION_VERIFIED = "ACTION_VERIFIED"

    # Customer messaging
    MESSAGE_GENERATED = "MESSAGE_GENERATED"
    MESSAGE_SENT = "MESSAGE_SENT"
    MESSAGE_DELIVERY_FAILED = "MESSAGE_DELIVERY_FAILED"
    CUSTOMER_OPT_OUT_SET = "CUSTOMER_OPT_OUT_SET"
    REPLY_RECEIVED = "REPLY_RECEIVED"
    REPLY_PARSED = "REPLY_PARSED"

    # Outcome
    PAYMENT_LINK_PAID = "PAYMENT_LINK_PAID"
    CASE_RECOVERED = "CASE_RECOVERED"
    CASE_FAILED = "CASE_FAILED"
    CASE_CLOSED = "CASE_CLOSED"

    # Human
    HUMAN_APPROVED = "HUMAN_APPROVED"
    HUMAN_REJECTED = "HUMAN_REJECTED"


class AuditActor(str, Enum):
    SYSTEM = "system"
    HUMAN = "human"
    WEBHOOK = "webhook"


class AuditLog(BaseModel):
    audit_id: str
    case_id: Optional[str] = None
    event_id: Optional[str] = None
    timestamp: datetime
    actor: AuditActor
    stage: str
    action: AuditAction
    details: Optional[dict[str, Any]] = None
