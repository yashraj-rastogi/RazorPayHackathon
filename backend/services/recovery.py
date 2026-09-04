"""
RevGuard — Recovery Execution Service (Layer E).

Handles:
- Creating Razorpay Payment Links with idempotency
- Generating customer messages via Gemini
- Sending messages via messaging provider
- Handling customer replies and opt-outs
- Timeout/unknown state verification
"""

import hashlib
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from backend.models.case import RecoveryCase, CaseStatus, PolicyDecisionType
from backend.models.action import RecoveryAction, ActionType, ActionStatus, CustomerMessage
from backend.models.audit import AuditAction, AuditActor
from backend.db.firestore import (
    get_document, set_document, update_document, query_collection, now_utc
)
from backend.services.audit import write_audit
from backend.services import policy as policy_service

logger = logging.getLogger(__name__)

MERCHANT_NAME = "DemoMerchant"


def _build_fallback_message(name: str, amount_rupees: float, link: str, language: str) -> str:
    """Deterministic multilingual recovery message (used when Gemini is unavailable)."""
    amt = f"₹{amount_rupees:,.0f}"
    if language == "hindi":
        return (
            f"नमस्ते {name}, आपका {amt} का सब्सक्रिप्शन भुगतान प्रोसेस नहीं हो सका। "
            f"कृपया इस लिंक से भुगतान पूरा करें: {link}"
        )
    elif language == "hinglish":
        return (
            f"Hi {name}, aapka {amt} ka subscription payment process nahi ho paya. "
            f"Please is link se payment complete karein: {link}"
        )
    else:
        return (
            f"Hi {name}, your subscription payment of Rs.{amount_rupees:,.0f} "
            f"could not be processed. Please use this link to complete payment: {link}"
        )


def _build_idempotency_key(case_id: str, action_type: str, attempt_count: int) -> str:
    """
    Deterministic idempotency key.
    Same case + same action + same attempt = same key = no duplicate.
    """
    raw = f"{case_id}:CREATE_PAYMENT_LINK:{attempt_count}"
    return "revguard-" + hashlib.sha256(raw.encode()).hexdigest()[:16]


def execute_recovery(case_id: str, phone_override: str | None = None) -> dict:
    """
    Execute recovery for an AUTO case.

    Steps:
    1. Load case — confirm it's still AUTO/ACTION_PENDING
    2. Re-check policy (do NOT trust old state)
    3. Check idempotency
    4. Create Razorpay Payment Link
    5. Generate Gemini customer message
    6. Store action + message
    7. Send message
    8. Write audit trail
    9. Return action

    Returns dict suitable for API response.
    """
    # 1. Load case
    case_doc = get_document("recovery_cases", case_id)
    if not case_doc:
        raise ValueError(f"Case not found: {case_id}")

    # Build RecoveryCase from doc
    from backend.models.case import RecoveryCase
    case = RecoveryCase(**{k: v for k, v in case_doc.items() if k != "_id"})

    # 2. Confirm policy is still AUTO
    if case.policy and case.policy.decision != PolicyDecisionType.AUTO:
        raise ValueError(f"Case {case_id} policy is {case.policy.decision}, not AUTO. Cannot recover.")

    if case.status == CaseStatus.CLOSED:
        raise ValueError(f"Case {case_id} is CLOSED. Cannot recover.")

    if case.status in (CaseStatus.RECOVERED,):
        logger.info("Case %s already RECOVERED — returning existing state.", case_id)
        return {"case_id": case_id, "status": "already_recovered"}

    # 3. Idempotency check
    event_doc = get_document("revenue_events", case.event_id) or {}
    attempt_count = event_doc.get("attempt_count", 1)
    idempotency_key = _build_idempotency_key(case_id, "CREATE_PAYMENT_LINK", attempt_count)

    existing_actions = query_collection(
        "recovery_actions",
        filters=[("case_id", "==", case_id), ("idempotency_key", "==", idempotency_key)],
        limit=1,
    )
    if existing_actions:
        existing = existing_actions[0]
        if existing.get("status") == ActionStatus.SUCCESS:
            logger.info("Idempotency: action already succeeded for case %s", case_id)
            return {
                "action_id": existing["action_id"],
                "status": "SUCCESS",
                "provider_reference": existing.get("provider_reference"),
                "recovery_url": existing.get("recovery_url"),
                "idempotent": True,
            }

    # 4. Load customer
    customer_doc = get_document("customers", case.customer_id) or {}
    from backend.models.customer import Customer
    from backend import config
    default_phone = config.TWILIO_TEST_PHONE_OVERRIDE or "+919876543210"
    target_phone = phone_override or customer_doc.get("phone") or default_phone
    customer = Customer(
        customer_id=case.customer_id,
        merchant_id=case.merchant_id,
        name=customer_doc.get("name", "Valued Customer"),
        phone=target_phone,
        email=customer_doc.get("email", "customer@example.com"),
        language_pref=customer_doc.get("language_pref", "english"),
        whatsapp_opt_in=True if phone_override else customer_doc.get("whatsapp_opt_in", True),
    )

    # Build action record
    action_id = f"act_{uuid.uuid4().hex[:12]}"
    action = RecoveryAction(
        action_id=action_id,
        case_id=case_id,
        action_type=ActionType.CREATE_PAYMENT_LINK,
        idempotency_key=idempotency_key,
        status=ActionStatus.EXECUTING,
        created_at=now_utc(),
    )
    set_document("recovery_actions", action_id, action.model_dump(mode="json"))

    # 5. Create Razorpay Payment Link
    payment_link_url = ""
    provider_reference = ""
    try:
        from backend.providers.razorpay import RazorpayProvider
        rp = RazorpayProvider()
        result = rp.create_recovery_payment_link(
            case_id=case_id,
            amount=case.amount,
            customer_name=customer.name,
            customer_email=customer.email,
            customer_phone=customer.phone,
            description=f"Recovery payment for subscription",
            idempotency_key=idempotency_key,
        )
        provider_reference = result.provider_reference
        payment_link_url = result.short_url

        update_document("recovery_actions", action_id, {
            "status": ActionStatus.SUCCESS,
            "provider_reference": provider_reference,
            "recovery_url": payment_link_url,
        })

        write_audit(
            action=AuditAction.ACTION_CREATED,
            stage="recovery",
            case_id=case_id,
            details={
                "action_id": action_id,
                "provider_reference": provider_reference,
                "amount": case.amount,
            },
        )

    except Exception as exc:
        # Timeout or network error → mark UNKNOWN, verify
        logger.error("Payment link creation failed for case %s: %s", case_id, exc)

        update_document("recovery_actions", action_id, {"status": ActionStatus.UNKNOWN})
        write_audit(
            action=AuditAction.ACTION_UNKNOWN,
            stage="recovery",
            case_id=case_id,
            details={"error": str(exc), "action_id": action_id},
        )
        # Return unknown status — caller must schedule verification
        return {
            "action_id": action_id,
            "status": "UNKNOWN",
            "error": str(exc),
            "message": "Payment link creation state unknown. Verification required.",
        }

    # 6. Generate customer message via Gemini
    message_data = None
    try:
        from backend.providers.gemini import GeminiClient
        gc = GeminiClient()
        message_data = gc.generate_recovery_message(
            case=case,
            customer=customer,
            payment_link_url=payment_link_url,
            merchant_name=MERCHANT_NAME,
        )

        write_audit(
            action=AuditAction.MESSAGE_GENERATED,
            stage="recovery",
            case_id=case_id,
            details={"language": message_data.get("language"), "prompt_version": "recovery_message_v1"},
        )

    except Exception as exc:
        logger.warning("Gemini message generation failed for case %s: %s", case_id, exc)
        # Fallback: deterministic multilingual message
        amount_rupees = case.amount / 100
        lang = customer.language_pref or "english"
        fallback_msg = _build_fallback_message(customer.name, amount_rupees, payment_link_url, lang)
        message_data = {
            "language": lang,
            "message": fallback_msg,
            "tone": "polite",
            "contains_factual_claims_only": True,
            "prompt_version": "fallback_v1",
            "generated_at": now_utc().isoformat(),
        }

    # 7. Store message in action doc
    customer_message = CustomerMessage(
        language=message_data.get("language", "english"),
        message=message_data["message"],
        tone=message_data.get("tone", "polite"),
        prompt_version=message_data.get("prompt_version", "recovery_message_v1"),
        generated_at=datetime.fromisoformat(message_data["generated_at"]) if "generated_at" in message_data else now_utc(),
    )

    update_document("recovery_actions", action_id, {
        "customer_message": customer_message.model_dump(mode="json"),
    })

    # 8. Send message
    send_phone = phone_override or customer.phone or config.TWILIO_TEST_PHONE_OVERRIDE
    if (customer.whatsapp_opt_in or phone_override) and send_phone:
        try:
            from backend.providers.messaging_mock import get_messaging_provider
            messaging = get_messaging_provider()
            logger.info("Dispatching recovery message to phone: %s via %s", send_phone, config.MESSAGING_PROVIDER)
            delivery = messaging.send(
                phone=send_phone,
                message=customer_message.message,
                case_id=case_id,
            )
            customer_message.sent = (delivery.status == "delivered")
            customer_message.sent_at = now_utc()
            customer_message.provider_reference = delivery.provider_reference

            update_document("recovery_actions", action_id, {
                "customer_message": customer_message.model_dump(mode="json"),
            })

            write_audit(
                action=AuditAction.MESSAGE_SENT,
                stage="recovery",
                case_id=case_id,
                details={"provider": delivery.provider, "reference": delivery.provider_reference},
            )

        except Exception as exc:
            logger.error("Message send failed for case %s: %s", case_id, exc)
            write_audit(
                action=AuditAction.MESSAGE_DELIVERY_FAILED,
                stage="recovery",
                case_id=case_id,
                details={"error": str(exc)},
            )
    else:
        logger.info("Skipping message for case %s: no phone or opted out", case_id)

    # 9. Update case status
    update_document("recovery_cases", case_id, {
        "status": CaseStatus.ACTION_SENT,
        "recovery_pending": True,
    })

    return {
        "action_id": action_id,
        "status": ActionStatus.SUCCESS,
        "provider": "razorpay",
        "provider_reference": provider_reference,
        "recovery_url": payment_link_url,
    }


def handle_customer_reply(reply_text: str, case_id: str, customer_id: str) -> dict:
    """
    Process a customer reply:
    - Extract intent via Gemini
    - Store CustomerReplyLog
    - Handle STOP → opt-out
    - Handle CONFUSED → flag for review
    - NEVER execute financial actions from reply text alone
    """
    from backend.models.action import CustomerReplyLog, ReplyIntent

    # Get customer language preference
    customer_doc = get_document("customers", customer_id) or {}
    language = customer_doc.get("language_pref", "english")

    write_audit(
        action=AuditAction.REPLY_RECEIVED,
        stage="customer",
        case_id=case_id,
        details={"customer_id": customer_id, "message_length": len(reply_text)},
    )

    # Extract intent via Gemini
    intent_data = {"intent": "OTHER", "promised_date": None, "confidence": 0.5}
    try:
        from backend.providers.gemini import GeminiClient
        gc = GeminiClient()
        intent_data = gc.extract_reply_intent(reply_text, language=language)
    except Exception as exc:
        logger.warning("Reply intent extraction failed: %s", exc)

    # Store reply log
    reply_id = f"reply_{uuid.uuid4().hex[:10]}"
    reply_log = CustomerReplyLog(
        reply_id=reply_id,
        case_id=case_id,
        customer_id=customer_id,
        raw_message=reply_text,
        intent=ReplyIntent(intent_data["intent"]),
        promised_date=intent_data.get("promised_date"),
        confidence=intent_data["confidence"],
        prompt_version=intent_data.get("prompt_version", "reply_intent_v1"),
        received_at=now_utc(),
        processed_at=now_utc(),
    )
    set_document("customer_replies", reply_id, reply_log.model_dump(mode="json"))

    write_audit(
        action=AuditAction.REPLY_PARSED,
        stage="customer",
        case_id=case_id,
        details={
            "intent": reply_log.intent,
            "confidence": reply_log.confidence,
            "promised_date": reply_log.promised_date,
        },
    )

    # Act on intent
    intent = reply_log.intent

    if intent == ReplyIntent.STOP:
        # Set opt-out on customer
        update_document("customers", customer_id, {"whatsapp_opt_in": False})
        write_audit(
            action=AuditAction.CUSTOMER_OPT_OUT_SET,
            stage="customer",
            case_id=case_id,
            details={"customer_id": customer_id, "source": "reply_intent"},
        )
        # Re-evaluate open AUTO cases for this customer → BLOCKED
        _block_open_cases_for_customer(customer_id)

    elif intent == ReplyIntent.CONFUSED:
        # Flag for review — do NOT auto-execute anything
        _flag_for_review(case_id)

    # PAY_NOW, ASK_TO_DELAY, OTHER — no automatic financial action
    return {
        "reply_id": reply_id,
        "intent": intent,
        "promised_date": reply_log.promised_date,
        "confidence": reply_log.confidence,
    }


def _block_open_cases_for_customer(customer_id: str):
    """Move all open AUTO cases for this customer to BLOCKED."""
    open_cases = query_collection(
        "recovery_cases",
        filters=[("customer_id", "==", customer_id), ("status", "==", CaseStatus.ACTION_PENDING)],
        limit=50,
    )
    for c in open_cases:
        update_document("recovery_cases", c["case_id"], {
            "status": CaseStatus.CLOSED,
            "policy.block_reason": "CUSTOMER_OPTED_OUT",
        })
        write_audit(
            action=AuditAction.CASE_CLOSED,
            stage="customer",
            case_id=c["case_id"],
            details={"reason": "Customer opted out via reply"},
        )


def _flag_for_review(case_id: str):
    """Move a case to QUEUED_FOR_REVIEW if not already."""
    case_doc = get_document("recovery_cases", case_id)
    if case_doc and case_doc.get("status") not in (
        CaseStatus.QUEUED_FOR_REVIEW, CaseStatus.CLOSED, CaseStatus.RECOVERED
    ):
        update_document("recovery_cases", case_id, {"status": CaseStatus.QUEUED_FOR_REVIEW})
        write_audit(
            action=AuditAction.DECISION_MADE,
            stage="policy",
            case_id=case_id,
            details={"decision": "QUEUE_FOR_REVIEW", "reason": "Customer replied CONFUSED"},
        )
