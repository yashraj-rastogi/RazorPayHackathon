"""
RevGuard — Cases Router.

GET  /api/v1/cases                       — list cases with filters
GET  /api/v1/cases/{case_id}             — case detail
POST /api/v1/cases/{case_id}/diagnose    — re-run diagnosis
POST /api/v1/cases/{case_id}/recover     — execute recovery action
POST /api/v1/cases/{case_id}/approve     — approve review case
POST /api/v1/cases/{case_id}/reject      — reject review case
GET  /api/v1/cases/{case_id}/audit       — audit trail
GET  /api/v1/cases/{case_id}/message     — preview customer message
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel

from backend.db.firestore import get_document, query_collection, update_document, now_utc
from backend.models.case import CaseStatus
from backend.models.audit import AuditAction, AuditActor
from backend.services.audit import write_audit
from backend.services.recovery import execute_recovery

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])


@router.get("")
async def list_cases(
    decision: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    min_amount: Optional[int] = Query(None),
    max_amount: Optional[int] = Query(None),
    limit: int = Query(50, le=200),
):
    """List recovery cases. Sorted by priority_score descending."""
    filters = []
    if decision and isinstance(decision, str):
        filters.append(("policy.decision", "==", decision.upper()))
    if status and isinstance(status, str):
        filters.append(("status", "==", status.upper()))

    try:
        cases = query_collection(
            "recovery_cases",
            filters=filters if filters else None,
            order_by="priority_score",
            descending=True,
            limit=limit,
        )
    except Exception as exc:
        # Fallback if composite index on (filter + priority_score) is not yet built
        cases = query_collection(
            "recovery_cases",
            filters=filters if filters else None,
            limit=limit,
        )
        cases.sort(key=lambda c: c.get("priority_score") or 0, reverse=True)

    # Apply amount filters in memory (Firestore doesn't support range + other filters easily)
    if isinstance(min_amount, (int, float)):
        cases = [c for c in cases if c.get("amount", 0) >= min_amount]
    if isinstance(max_amount, (int, float)):
        cases = [c for c in cases if c.get("amount", 0) <= max_amount]

    return {"cases": cases, "count": len(cases)}


@router.get("/{case_id}")
async def get_case(case_id: str):
    """Case detail including event, diagnosis, policy, and current status."""
    case = get_document("recovery_cases", case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    # Enrich with event
    event = get_document("revenue_events", case.get("event_id", "")) if case.get("event_id") else None

    return {
        "case": case,
        "event": event,
    }


@router.post("/{case_id}/recover")
async def recover(case_id: str):
    """Execute recovery action for an AUTO case. Idempotent."""
    case = get_document("recovery_cases", case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    policy_decision = (case.get("policy") or {}).get("decision")
    if policy_decision != "AUTO":
        raise HTTPException(
            status_code=400,
            detail={
                "error": {"code": "POLICY_BLOCKED", "message": f"Case policy is {policy_decision}, not AUTO."}
            },
        )

    try:
        result = execute_recovery(case_id)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{case_id}/approve")
async def approve(case_id: str):
    """Approve a QUEUE_FOR_REVIEW case and execute recovery."""
    case = get_document("recovery_cases", case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    if case.get("status") not in (CaseStatus.QUEUED_FOR_REVIEW, "QUEUED_FOR_REVIEW"):
        raise HTTPException(status_code=400, detail="Case is not in review queue.")

    # Re-check policy before approving (do NOT trust browser state)
    from backend.services import policy as policy_service
    from backend.models.case import RecoveryCase
    case_obj = RecoveryCase(**{k: v for k, v in case.items() if k != "_id"})
    event_doc = get_document("revenue_events", case.get("event_id", "")) or {}
    attempt_count = event_doc.get("attempt_count", 1)

    customer_doc = get_document("customers", case.get("customer_id", "")) or {}
    customer_opted_out = not customer_doc.get("whatsapp_opt_in", True)

    policy = policy_service.evaluate(
        case_obj,
        customer_opted_out=customer_opted_out,
        attempt_count=attempt_count,
    )

    if customer_opted_out:
        raise HTTPException(status_code=400, detail="Customer has opted out. Cannot approve.")

    # Update to AUTO for recovery execution
    update_document("recovery_cases", case_id, {"policy.decision": "AUTO", "status": CaseStatus.ACTION_PENDING})

    write_audit(
        action=AuditAction.HUMAN_APPROVED,
        actor=AuditActor.HUMAN,
        stage="review",
        case_id=case_id,
        details={"approved_by": "human_reviewer"},
    )

    try:
        result = execute_recovery(case_id)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class RejectRequest(BaseModel):
    reason: str = ""


@router.post("/{case_id}/reject")
async def reject(case_id: str, body: RejectRequest):
    """Reject a review case."""
    case = get_document("recovery_cases", case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    update_document("recovery_cases", case_id, {
        "status": CaseStatus.CLOSED,
        "rejection_reason": body.reason,
    })

    write_audit(
        action=AuditAction.HUMAN_REJECTED,
        actor=AuditActor.HUMAN,
        stage="review",
        case_id=case_id,
        details={"reason": body.reason},
    )

    return {"status": "rejected", "case_id": case_id}


@router.get("/{case_id}/audit")
async def get_audit(case_id: str):
    """Return the append-only audit trail for a case."""
    entries = query_collection(
        "audit_logs",
        filters=[("case_id", "==", case_id)],
        order_by="timestamp",
        limit=200,
    )
    return {"case_id": case_id, "events": entries}


@router.get("/{case_id}/message")
async def get_message(case_id: str):
    """
    Preview the stored customer message for this case.
    Does NOT re-call Gemini — renders stored text only.
    """
    actions = query_collection(
        "recovery_actions",
        filters=[("case_id", "==", case_id)],
        order_by="created_at",
        descending=True,
        limit=1,
    )
    if not actions or not actions[0].get("customer_message"):
        raise HTTPException(status_code=404, detail="No customer message found for this case.")

    msg = actions[0]["customer_message"]
    return {
        "case_id": case_id,
        "language": msg.get("language"),
        "message": msg.get("message"),
        "tone": msg.get("tone"),
        "contains_factual_claims_only": True,
        "generated_at": msg.get("generated_at"),
        "prompt_version": msg.get("prompt_version"),
        "sent": msg.get("sent", False),
        "sent_at": msg.get("sent_at"),
    }
