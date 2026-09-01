"""
RevGuard — RecoveryAction and CustomerReplyLog models.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class ActionType(str, Enum):
    CREATE_PAYMENT_LINK = "CREATE_PAYMENT_LINK"
    SEND_MESSAGE = "SEND_MESSAGE"
    SCHEDULE_FOLLOWUP = "SCHEDULE_FOLLOWUP"
    QUEUE_FOR_REVIEW = "QUEUE_FOR_REVIEW"
    BLOCK = "BLOCK"


class ActionStatus(str, Enum):
    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"  # Network timeout — must verify


class CustomerMessage(BaseModel):
    language: str
    message: str
    tone: str = "polite"
    prompt_version: str = ""
    generated_at: Optional[datetime] = None
    sent: bool = False
    sent_at: Optional[datetime] = None
    provider_reference: Optional[str] = None


class RecoveryAction(BaseModel):
    action_id: str
    case_id: str
    action_type: ActionType
    autonomy_level: str = "AUTO"
    idempotency_key: str
    status: ActionStatus = ActionStatus.PENDING
    provider: str = "razorpay"
    provider_reference: Optional[str] = None  # plink_xxx — must be top-level for Firestore index
    recovery_url: Optional[str] = None
    customer_message: Optional[CustomerMessage] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ReplyIntent(str, Enum):
    PAY_NOW = "PAY_NOW"
    ASK_TO_DELAY = "ASK_TO_DELAY"
    STOP = "STOP"
    CONFUSED = "CONFUSED"
    OTHER = "OTHER"


class CustomerReplyLog(BaseModel):
    reply_id: str
    case_id: str
    customer_id: str
    raw_message: str
    intent: ReplyIntent
    promised_date: Optional[str] = None  # YYYY-MM-DD or null
    confidence: float
    prompt_version: str = "reply_intent_v1"
    received_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
