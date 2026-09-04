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


class PitchScenarioRequest(BaseModel):
    phone_override: Optional[str] = None


@router.post("/pitch-scenario")
async def pitch_scenario(payload: Optional[PitchScenarioRequest] = None):
    """
    1-Click Pitch Walkthrough Scenario:
    1. Ingests a simulated high-confidence recurring failure (Rs.2,499).
    2. Diagnoses root cause via deterministic/Gemini engine.
    3. Runs policy engine verification.
    4. Executes recovery (creates real Razorpay Payment Link + customer message).
    5. Returns all telemetric state for live cockpit animation.
    """
    from backend.models.event import NormalizedRevenueEvent
    from backend.services.ingestion import ingest_event
    from backend.services.recovery import execute_recovery
    import uuid

    phone = payload.phone_override if payload else None

    event_id = f"evt_pitch_{uuid.uuid4().hex[:8]}"
    event = NormalizedRevenueEvent(
        event_id=event_id,
        merchant_id="merch_saas_prime",
        customer_id="cust_pro_vip",
        subscription_id="sub_annual_pro",
        amount=249900,  # Rs. 2,499
        currency="INR",
        reason="BANK_TIMEOUT",
        gateway_message="NPCI UPI Autopay mandate debit timed out at destination issuer CBS core.",
        attempt_count=1,
    )

    # 1. Ingest & Diagnose & Policy
    ingest_result = ingest_event(event)
    case_id = ingest_result["case_id"]

    # 2. If policy queued for review, approve it for demo execution
    from backend.db.firestore import update_document, get_document
    case_doc = get_document("recovery_cases", case_id) or {}
    if case_doc.get("policy", {}).get("decision") != "AUTO":
        update_document("recovery_cases", case_id, {"policy.decision": "AUTO", "status": "ACTION_PENDING"})

    # 3. Execute Recovery (Razorpay Link + WhatsApp Outreach)
    recovery_result = execute_recovery(case_id, phone_override=phone)

    return {
        "status": "success",
        "case_id": case_id,
        "event": {
            "event_id": event.event_id,
            "amount": event.amount,
            "currency": "INR",
            "reason": event.reason,
            "gateway_message": event.gateway_message,
        },
        "diagnosis": ingest_result.get("case", {}).get("diagnosis", {}),
        "policy": ingest_result.get("case", {}).get("policy", {}),
        "recovery": {
            "action_id": recovery_result.get("action_id"),
            "provider_reference": recovery_result.get("provider_reference"),
            "recovery_url": recovery_result.get("recovery_url"),
            "status": recovery_result.get("status"),
        }
    }
