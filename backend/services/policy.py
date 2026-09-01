"""
RevGuard — Policy Engine (Layer D).

Thresholds come exclusively from config.py.
Order matters: BLOCKED checks first, then QUEUE_FOR_REVIEW, then AUTO.
"""

import logging
from backend.models.case import (
    RecoveryCase, PolicyDecision, PolicyDecisionType, DiagnosisBucket, CaseStatus
)
from backend import config

logger = logging.getLogger(__name__)

# Failure buckets that are never recoverable via payment link
NON_RECOVERABLE_BUCKETS = {
    DiagnosisBucket.MANDATE_INACTIVE,
}

# Failure types that do NOT route to deterministic BLOCKED (handled upstream)
# but still may have confidence below threshold
RECOVERABLE_BUCKETS = {
    DiagnosisBucket.TEMPORARY_FAILURE,
    DiagnosisBucket.INSUFFICIENT_FUNDS,
    DiagnosisBucket.PAYMENT_CREDENTIAL_EXPIRED,
    DiagnosisBucket.OTP_OR_AUTHENTICATION_ISSUE,
    DiagnosisBucket.UNKNOWN,
}


def evaluate(
    case: RecoveryCase,
    *,
    payment_already_succeeded: bool = False,
    mandate_is_inactive: bool = False,
    customer_opted_out: bool = False,
    attempt_count: int = 1,
) -> PolicyDecision:
    """
    Deterministic policy evaluation.
    All thresholds are read from config — never hardcoded here.

    Returns a PolicyDecision with reasons explaining the outcome.
    """
    diagnosis = case.diagnosis

    # ── BLOCKED checks (order matters) ──────────────────────────
    if payment_already_succeeded:
        return PolicyDecision(
            decision=PolicyDecisionType.BLOCKED,
            block_reason="PAYMENT_ALREADY_SUCCEEDED",
            reasons=["Payment confirmed already succeeded — no action needed."],
        )

    if mandate_is_inactive:
        return PolicyDecision(
            decision=PolicyDecisionType.BLOCKED,
            block_reason="MANDATE_INACTIVE",
            reasons=["Subscription mandate is inactive — payment link cannot recover this."],
        )

    if customer_opted_out:
        return PolicyDecision(
            decision=PolicyDecisionType.BLOCKED,
            block_reason="CUSTOMER_OPTED_OUT",
            reasons=["Customer has opted out of WhatsApp outreach."],
        )

    if diagnosis and diagnosis.bucket in NON_RECOVERABLE_BUCKETS:
        return PolicyDecision(
            decision=PolicyDecisionType.BLOCKED,
            block_reason="NON_RECOVERABLE_BUCKET",
            reasons=[f"Failure bucket '{diagnosis.bucket}' is not recoverable via payment link."],
        )

    # ── QUEUE_FOR_REVIEW checks ──────────────────────────────────
    if not diagnosis:
        return PolicyDecision(
            decision=PolicyDecisionType.QUEUE_FOR_REVIEW,
            reasons=["No diagnosis available — manual review required."],
        )

    if diagnosis.confidence < config.POLICY_MIN_CONFIDENCE_AUTO:
        return PolicyDecision(
            decision=PolicyDecisionType.QUEUE_FOR_REVIEW,
            reasons=[
                f"AI confidence {diagnosis.confidence:.2f} < threshold {config.POLICY_MIN_CONFIDENCE_AUTO}.",
                f"Diagnosis method: {diagnosis.method}.",
            ],
        )

    if case.amount >= config.POLICY_MAX_AMOUNT_AUTO:
        amount_rupees = case.amount / 100
        threshold_rupees = config.POLICY_MAX_AMOUNT_AUTO / 100
        return PolicyDecision(
            decision=PolicyDecisionType.QUEUE_FOR_REVIEW,
            reasons=[
                f"Amount Rs.{amount_rupees:,.0f} >= threshold Rs.{threshold_rupees:,.0f}.",
                "High-value cases require human approval.",
            ],
        )

    if attempt_count >= config.POLICY_MAX_RETRY_AUTO:
        return PolicyDecision(
            decision=PolicyDecisionType.QUEUE_FOR_REVIEW,
            reasons=[
                f"Attempt count {attempt_count} >= limit {config.POLICY_MAX_RETRY_AUTO}.",
                "Multiple retries exhausted — manual review required.",
            ],
        )

    # ── AUTO ────────────────────────────────────────────────────
    amount_rupees = case.amount / 100
    threshold_rupees = config.POLICY_MAX_AMOUNT_AUTO / 100
    return PolicyDecision(
        decision=PolicyDecisionType.AUTO,
        reasons=[
            f"Confidence {diagnosis.confidence:.2f} >= {config.POLICY_MIN_CONFIDENCE_AUTO}.",
            f"Amount Rs.{amount_rupees:,.0f} < threshold Rs.{threshold_rupees:,.0f}.",
            f"Attempt count {attempt_count} < {config.POLICY_MAX_RETRY_AUTO}.",
            f"Failure bucket '{diagnosis.bucket}' is recoverable.",
        ],
        policy_version=config.POLICY_VERSION,
    )
