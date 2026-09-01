"""
RevGuard — Event Ingestion Service (Layer A).

Orchestrates the full event → diagnosis → scoring → policy pipeline.
Handles idempotency: duplicate events are silently dropped with an audit entry.
"""

import uuid
import logging
from datetime import datetime, timezone

from backend.models.event import NormalizedRevenueEvent
from backend.models.case import RecoveryCase, CaseStatus, PolicyDecisionType
from backend.models.audit import AuditAction, AuditActor
from backend.db.firestore import (
    get_document, set_document, update_document, now_utc
)
from backend.services import diagnosis as diagnosis_service
from backend.services import scoring as scoring_service
from backend.services import policy as policy_service
from backend.services.audit import write_audit

logger = logging.getLogger(__name__)


def ingest_event(event: NormalizedRevenueEvent) -> dict:
    """
    Full ingestion pipeline.

    Returns dict with:
      - case_id
      - policy_decision
      - is_duplicate (bool)
      - case (RecoveryCase)
    """
    # ── Idempotency: check for duplicate event ───────────────────
    existing_event = get_document("revenue_events", event.event_id)
    if existing_event:
        logger.info("Duplicate event detected: %s", event.event_id)
        write_audit(
            action=AuditAction.DUPLICATE_EVENT_BLOCKED,
            stage="ingestion",
            event_id=event.event_id,
            details={"event_id": event.event_id},
        )
        existing_case_id = existing_event.get("case_id")
        existing_case = get_document("recovery_cases", existing_case_id) if existing_case_id else None
        return {
            "case_id": existing_case_id,
            "policy_decision": None,
            "is_duplicate": True,
            "case": existing_case,
        }

    # ── Store the event ─────────────────────────────────────────
    event_dict = event.model_dump(mode="json")
    event_dict["created_at"] = now_utc().isoformat()
    set_document("revenue_events", event.event_id, event_dict)

    write_audit(
        action=AuditAction.EVENT_RECEIVED,
        stage="ingestion",
        event_id=event.event_id,
        details={
            "merchant_id": event.merchant_id,
            "amount": event.amount,
            "reason": event.reason,
        },
    )

    # ── Create recovery case ─────────────────────────────────────
    case_id = f"case_{uuid.uuid4().hex[:12]}"
    case = RecoveryCase(
        case_id=case_id,
        event_id=event.event_id,
        merchant_id=event.merchant_id,
        customer_id=event.customer_id,
        amount=event.amount,
        status=CaseStatus.NEW,
        created_at=now_utc(),
        updated_at=now_utc(),
    )

    # Store event → case link
    update_document("revenue_events", event.event_id, {"case_id": case_id})

    # ── Diagnosis ────────────────────────────────────────────────
    diag = diagnosis_service.diagnose(event)
    case.diagnosis = diag
    case.status = CaseStatus.DIAGNOSED

    write_audit(
        action=AuditAction.DIAGNOSIS_COMPLETED,
        stage="diagnosis",
        case_id=case_id,
        event_id=event.event_id,
        details={
            "bucket": diag.bucket,
            "confidence": diag.confidence,
            "method": diag.method,
        },
    )

    # ── Scoring ──────────────────────────────────────────────────
    case = scoring_service.score(case, attempt_count=event.attempt_count)

    # ── Look up customer for policy context ──────────────────────
    customer_doc = get_document("customers", event.customer_id)
    customer_opted_out = not customer_doc.get("whatsapp_opt_in", True) if customer_doc else False

    # ── Policy evaluation ────────────────────────────────────────
    # Check if mandate is inactive based on diagnosis bucket
    from backend.models.case import DiagnosisBucket
    mandate_inactive = diag.bucket == DiagnosisBucket.MANDATE_INACTIVE

    # Check if payment already succeeded (look up reason code)
    payment_already_succeeded = event.reason.upper() == "ALREADY_PAID"

    policy = policy_service.evaluate(
        case,
        payment_already_succeeded=payment_already_succeeded,
        mandate_is_inactive=mandate_inactive,
        customer_opted_out=customer_opted_out,
        attempt_count=event.attempt_count,
    )
    case.policy = policy
    case.status = CaseStatus.POLICY_EVALUATED

    write_audit(
        action=AuditAction.DECISION_MADE,
        stage="policy",
        case_id=case_id,
        event_id=event.event_id,
        details={
            "decision": policy.decision,
            "reasons": policy.reasons,
            "priority_score": case.priority_score,
        },
    )

    # ── Determine terminal status ────────────────────────────────
    if policy.decision == PolicyDecisionType.BLOCKED:
        case.status = CaseStatus.CLOSED
    elif policy.decision == PolicyDecisionType.QUEUE_FOR_REVIEW:
        case.status = CaseStatus.QUEUED_FOR_REVIEW
    else:
        case.status = CaseStatus.ACTION_PENDING

    # ── Persist case ─────────────────────────────────────────────
    case_dict = case.model_dump(mode="json")
    set_document("recovery_cases", case_id, case_dict)

    return {
        "case_id": case_id,
        "policy_decision": policy.decision,
        "is_duplicate": False,
        "case": case_dict,
    }
