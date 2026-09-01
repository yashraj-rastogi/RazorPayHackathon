"""
RevGuard — Simulate Router (dev/demo only).
POST /api/v1/simulate/failure — inject failure scenarios for testing.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v1/simulate", tags=["simulate"])

ALLOWED_TYPES = {
    "razorpay_timeout",
    "gemini_timeout",
    "malformed_ai_output",
    "duplicate_event",
    "already_successful",
    "retry_limit",
}


class SimulateRequest(BaseModel):
    type: str
    case_id: Optional[str] = None


@router.post("/failure")
async def simulate_failure(req: SimulateRequest):
    """
    Inject a failure scenario for testing/demo purposes.
    This endpoint exists only to reproduce failure handling during testing.
    """
    if req.type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unknown simulation type: {req.type}. Allowed: {ALLOWED_TYPES}")

    from backend.models.event import NormalizedRevenueEvent
    from backend.services.ingestion import ingest_event
    import uuid

    if req.type == "duplicate_event":
        # Create one event then ingest it twice
        event = NormalizedRevenueEvent(
            event_id=f"sim_dup_{uuid.uuid4().hex[:8]}",
            merchant_id="m_001",
            customer_id="c_001",
            subscription_id="sub_sim_001",
            amount=49900,
            reason="BANK_TIMEOUT",
            gateway_message="Simulated duplicate",
            attempt_count=1,
        )
        result1 = ingest_event(event)
        result2 = ingest_event(event)  # Should be blocked
        return {
            "simulation": "duplicate_event",
            "first_ingest": result1,
            "second_ingest": result2,
            "idempotency_verified": result2["is_duplicate"],
        }

    elif req.type == "already_successful":
        event = NormalizedRevenueEvent(
            event_id=f"sim_success_{uuid.uuid4().hex[:8]}",
            merchant_id="m_001",
            customer_id="c_001",
            subscription_id="sub_sim_001",
            amount=49900,
            reason="ALREADY_PAID",
            gateway_message="Payment already processed",
            attempt_count=1,
        )
        result = ingest_event(event)
        return {"simulation": "already_successful", "result": result}

    elif req.type == "retry_limit":
        event = NormalizedRevenueEvent(
            event_id=f"sim_retry_{uuid.uuid4().hex[:8]}",
            merchant_id="m_001",
            customer_id="c_001",
            subscription_id="sub_sim_001",
            amount=49900,
            reason="BANK_TIMEOUT",
            gateway_message="Simulated retry limit",
            attempt_count=3,
        )
        result = ingest_event(event)
        return {"simulation": "retry_limit", "result": result}

    elif req.type == "gemini_timeout":
        event = NormalizedRevenueEvent(
            event_id=f"sim_gemini_{uuid.uuid4().hex[:8]}",
            merchant_id="m_001",
            customer_id="c_001",
            subscription_id="sub_sim_001",
            amount=49900,
            reason="UNKNOWN_GATEWAY_ERROR",
            gateway_message="Unexpected issuer response while processing mandate debit.",
            attempt_count=1,
        )
        result = ingest_event(event)
        return {"simulation": "gemini_timeout", "result": result}

    return {"simulation": req.type, "status": "not_yet_implemented"}
