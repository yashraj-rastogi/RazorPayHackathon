"""
RevGuard — DiagnosisResult, PolicyDecision, and RecoveryCase models.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class DiagnosisBucket(str, Enum):
    TEMPORARY_FAILURE = "temporary_failure"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    PAYMENT_CREDENTIAL_EXPIRED = "payment_credential_expired"
    MANDATE_INACTIVE = "mandate_inactive"
    OTP_OR_AUTHENTICATION_ISSUE = "otp_or_authentication_issue"
    UNKNOWN = "unknown"


class DiagnosisMethod(str, Enum):
    DETERMINISTIC = "deterministic"
    GEMINI = "gemini"
    FALLBACK = "fallback"


class DiagnosisResult(BaseModel):
    bucket: DiagnosisBucket
    confidence: float  # 0.0 – 1.0
    method: DiagnosisMethod
    explanation: str = ""
    evidence_summary: Optional[str] = None
    uncertainty: Optional[str] = None
    prompt_version: Optional[str] = None
    model_id: Optional[str] = None


class PolicyDecisionType(str, Enum):
    AUTO = "AUTO"
    QUEUE_FOR_REVIEW = "QUEUE_FOR_REVIEW"
    BLOCKED = "BLOCKED"


class PolicyDecision(BaseModel):
    decision: PolicyDecisionType
    policy_version: str = "v1"
    reasons: list[str] = []
    block_reason: Optional[str] = None


class CaseStatus(str, Enum):
    NEW = "NEW"
    DIAGNOSED = "DIAGNOSED"
    POLICY_EVALUATED = "POLICY_EVALUATED"
    # AUTO path
    ACTION_PENDING = "ACTION_PENDING"
    ACTION_SENT = "ACTION_SENT"
    RECOVERY_PENDING = "RECOVERY_PENDING"
    RECOVERED = "RECOVERED"
    FAILED = "FAILED"
    # REVIEW path
    QUEUED_FOR_REVIEW = "QUEUED_FOR_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    # BLOCKED path
    CLOSED = "CLOSED"


class RecoverabilityLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class RecoveryCase(BaseModel):
    case_id: str
    event_id: str
    merchant_id: str
    customer_id: str
    amount: int  # paise
    recoverability: Optional[RecoverabilityLevel] = None
    recovery_probability: Optional[float] = None
    priority_score: Optional[int] = None
    diagnosis: Optional[DiagnosisResult] = None
    policy: Optional[PolicyDecision] = None
    attempt_count: Optional[int] = 1
    status: CaseStatus = CaseStatus.NEW
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
