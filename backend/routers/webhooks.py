"""
RevGuard — Razorpay Webhook Router.

POST /api/v1/webhooks/razorpay

CRITICAL: Always return HTTP 200, even for unknown events.
Non-2xx causes Razorpay to retry → potential duplicate processing.
"""

import hmac
import hashlib
import json
import logging
import os
from fastapi import APIRouter, Request, Response, HTTPException

from backend.db.firestore import query_collection, update_document, now_utc
from backend.models.case import CaseStatus
from backend.models.audit import AuditAction, AuditActor
from backend.services.audit import write_audit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")


def _verify_signature(payload_bytes: bytes, signature: str, secret: str) -> bool:
    """Verify Razorpay HMAC-SHA256 webhook signature."""
    if not secret:
        logger.warning("RAZORPAY_WEBHOOK_SECRET not set — skipping signature verification.")
        return True  # Allow through in dev; lock down in production
    expected = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/razorpay")
async def razorpay_webhook(request: Request):
    """
    Handle incoming Razorpay webhooks.
    Supports: payment_link.paid

    Rules:
    - Verify HMAC signature
    - Idempotent processing
    - ALWAYS return 200 (even for unknown events)
    """
    payload_bytes = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    # 1. Verify signature
    if not _verify_signature(payload_bytes, signature, WEBHOOK_SECRET):
        logger.warning("Invalid webhook signature — rejecting.")
        raise HTTPException(status_code=400, detail="Invalid signature.")

    # Parse payload
    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError:
        logger.error("Webhook payload is not valid JSON.")
        return Response(status_code=200)

    event_type = payload.get("event", "")
    logger.info("Received Razorpay webhook: %s", event_type)

    # 2. Handle payment_link.paid
    if event_type == "payment_link.paid":
        await _handle_payment_link_paid(payload)

    # 3. Return 200 for ALL events — including unknown ones
    return Response(status_code=200)


async def _handle_payment_link_paid(payload: dict):
    """
    Mark case RECOVERED when payment link is paid.
    Lookup is by provider_reference (plink_xxx) — not by case_id.
    """
    try:
        # Extract payment link ID from Razorpay webhook payload
        payment_link = payload.get("payload", {}).get("payment_link", {}).get("entity", {})
        plink_id = payment_link.get("id", "")

        if not plink_id:
            logger.warning("payment_link.paid webhook missing payment link ID.")
            return

        # 3. Query recovery_actions by provider_reference
        # IMPORTANT: provider_reference is a top-level field — Firestore can index it
        matching_actions = query_collection(
            "recovery_actions",
            filters=[("provider_reference", "==", plink_id)],
            limit=1,
        )

        if not matching_actions:
            logger.warning("No recovery action found for plink_id: %s", plink_id)
            return

        action = matching_actions[0]
        case_id = action.get("case_id")
        action_id = action.get("action_id")

        # 4. Idempotency: check if already RECOVERED
        if action.get("status") == "SUCCESS" and (
            action.get("completed_at") is not None
        ):
            # Check if case is already RECOVERED
            from backend.db.firestore import get_document
            case_doc = get_document("recovery_cases", case_id)
            if case_doc and case_doc.get("status") == CaseStatus.RECOVERED:
                logger.info("Idempotent webhook: case %s already RECOVERED", case_id)
                return

        # 5. Mark action SUCCESS
        update_document("recovery_actions", action_id, {
            "status": "SUCCESS",
            "completed_at": now_utc().isoformat(),
        })

        # 6. Mark case RECOVERED
        update_document("recovery_cases", case_id, {
            "status": CaseStatus.RECOVERED,
        })

        # 7. Write audit
        write_audit(
            action=AuditAction.PAYMENT_LINK_PAID,
            actor=AuditActor.WEBHOOK,
            stage="outcome",
            case_id=case_id,
            details={"plink_id": plink_id, "action_id": action_id},
        )
        write_audit(
            action=AuditAction.CASE_RECOVERED,
            actor=AuditActor.WEBHOOK,
            stage="outcome",
            case_id=case_id,
            details={"plink_id": plink_id},
        )

        logger.info("Case %s marked RECOVERED via webhook (plink: %s)", case_id, plink_id)

    except Exception as exc:
        logger.error("Error handling payment_link.paid webhook: %s", exc)
        # Do NOT re-raise — we must return 200


@router.post("/twilio-reply")
async def twilio_reply_webhook(request: Request):
    """
    Handle inbound WhatsApp replies from Twilio.

    Twilio sends form-urlencoded POST with:
    - Body: the message text
    - From: whatsapp:+91...
    - To: whatsapp:+14155238886

    We extract intent (PAY_NOW, STOP, ASK_TO_DELAY, CONFUSED, OTHER)
    and act accordingly. STOP → opt-out. CONFUSED → flag for review.
    PAY_NOW / ASK_TO_DELAY → log only (no financial action).
    """
    form = await request.form()
    body = form.get("Body", "")
    from_number = form.get("From", "")

    if not body:
        logger.warning("Twilio reply webhook: empty body.")
        return Response(content="<Response></Response>", media_type="application/xml", status_code=200)

    logger.info("Inbound WhatsApp reply from %s: %s", from_number, body[:100])

    # Find the most recent case associated with this phone number
    # Look up customer by phone
    phone_clean = from_number.replace("whatsapp:", "")
    case_id = None
    customer_id = None

    try:
        customers = query_collection(
            "customers",
            filters=[("phone", "==", phone_clean)],
            limit=1,
        )
        if customers:
            customer_id = customers[0].get("customer_id")
            # Find most recent open case for this customer
            cases = query_collection(
                "recovery_cases",
                filters=[("customer_id", "==", customer_id)],
                limit=1,
            )
            if cases:
                case_id = cases[0].get("case_id")
    except Exception as exc:
        logger.warning("Could not find customer/case for phone %s: %s", phone_clean, exc)

    if not case_id or not customer_id:
        logger.info("No matching case found for reply from %s — logging only.", from_number)
        write_audit(
            action=AuditAction.REPLY_RECEIVED,
            stage="customer",
            case_id=case_id or "UNKNOWN",
            details={"from": from_number, "body_preview": body[:80], "matched": False},
        )
        return Response(content="<Response></Response>", media_type="application/xml", status_code=200)

    # Process reply via recovery service
    try:
        from backend.services.recovery import handle_customer_reply
        result = handle_customer_reply(
            reply_text=body,
            case_id=case_id,
            customer_id=customer_id,
        )
        logger.info("Reply processed for case %s: intent=%s, confidence=%.2f",
                     case_id, result["intent"], result["confidence"])
    except Exception as exc:
        logger.error("Error processing customer reply for case %s: %s", case_id, exc)

    # Return TwiML empty response (Twilio expects XML)
    return Response(content="<Response></Response>", media_type="application/xml", status_code=200)
