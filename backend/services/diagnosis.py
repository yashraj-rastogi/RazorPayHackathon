"""
RevGuard — Failure Diagnosis Service (Layer B).

Strategy:
1. Try deterministic mapping table (no API call, instant, 100% confidence).
2. If reason code is unknown, call Gemini only for that case.
3. On Gemini failure, fall back to deterministic if possible, else QUEUE_FOR_REVIEW.
"""

import logging
from backend.models.event import NormalizedRevenueEvent
from backend.models.case import DiagnosisResult, DiagnosisBucket, DiagnosisMethod

logger = logging.getLogger(__name__)

# ─── Deterministic Mapping Table ────────────────────────────────
# Maps gateway reason codes → (bucket, confidence)
# High confidence because the mapping is authoritative.
KNOWN_CODES: dict[str, tuple[str, float]] = {
    "BANK_TIMEOUT":          (DiagnosisBucket.TEMPORARY_FAILURE, 0.97),
    "GATEWAY_TIMEOUT":       (DiagnosisBucket.TEMPORARY_FAILURE, 0.96),
    "ISSUER_TIMEOUT":        (DiagnosisBucket.TEMPORARY_FAILURE, 0.95),
    "NETWORK_ERROR":         (DiagnosisBucket.TEMPORARY_FAILURE, 0.93),
    "INSUFFICIENT_FUNDS":    (DiagnosisBucket.INSUFFICIENT_FUNDS, 0.99),
    "BALANCE_TOO_LOW":       (DiagnosisBucket.INSUFFICIENT_FUNDS, 0.98),
    "LOW_BALANCE":           (DiagnosisBucket.INSUFFICIENT_FUNDS, 0.97),
    "CARD_EXPIRED":          (DiagnosisBucket.PAYMENT_CREDENTIAL_EXPIRED, 0.99),
    "CARD_INVALID":          (DiagnosisBucket.PAYMENT_CREDENTIAL_EXPIRED, 0.97),
    "VPA_EXPIRED":           (DiagnosisBucket.PAYMENT_CREDENTIAL_EXPIRED, 0.96),
    "MANDATE_CANCELLED":     (DiagnosisBucket.MANDATE_INACTIVE, 0.99),
    "MANDATE_REVOKED":       (DiagnosisBucket.MANDATE_INACTIVE, 0.99),
    "MANDATE_PAUSED":        (DiagnosisBucket.MANDATE_INACTIVE, 0.97),
    "OTP_FAILED":            (DiagnosisBucket.OTP_OR_AUTHENTICATION_ISSUE, 0.95),
    "AUTH_FAILED":           (DiagnosisBucket.OTP_OR_AUTHENTICATION_ISSUE, 0.93),
    "AUTHENTICATION_FAILED": (DiagnosisBucket.OTP_OR_AUTHENTICATION_ISSUE, 0.93),
    "DEBIT_LIMIT_REACHED":   (DiagnosisBucket.INSUFFICIENT_FUNDS, 0.88),
    # These are not really recoverable — but we still classify them for audit completeness
    "ALREADY_PAID":          (DiagnosisBucket.UNKNOWN, 0.99),
    "OPT_OUT":               (DiagnosisBucket.UNKNOWN, 0.99),
    "RETRY_LIMIT":           (DiagnosisBucket.UNKNOWN, 0.99),
}

# Codes that, if Gemini is unavailable, still have a deterministic fallback
FALLBACK_CODES: dict[str, tuple[str, float]] = {
    "UNKNOWN_GATEWAY_ERROR": (DiagnosisBucket.UNKNOWN, 0.50),
    "GENERIC_DECLINE":       (DiagnosisBucket.UNKNOWN, 0.45),
    "SYSTEM_ERROR":          (DiagnosisBucket.TEMPORARY_FAILURE, 0.65),
}


def diagnose(event: NormalizedRevenueEvent) -> DiagnosisResult:
    """
    Main entry point. Returns a DiagnosisResult.
    Gemini is called only for codes not in KNOWN_CODES.
    """
    reason = event.reason.upper()

    # 1. Try deterministic mapping
    if reason in KNOWN_CODES:
        bucket, confidence = KNOWN_CODES[reason]
        logger.debug("Deterministic diagnosis: %s → %s (%.2f)", reason, bucket, confidence)
        return DiagnosisResult(
            bucket=bucket,
            confidence=confidence,
            method=DiagnosisMethod.DETERMINISTIC,
            explanation=f"Reason code '{reason}' deterministically mapped to {bucket}.",
        )

    # 2. Unknown code → call Gemini
    logger.info("Unknown reason code '%s' → sending to Gemini for diagnosis", reason)
    return _gemini_diagnose(event)


def _gemini_diagnose(event: NormalizedRevenueEvent) -> DiagnosisResult:
    """
    Call Gemini for ambiguous failure codes.
    Falls back gracefully if Gemini is unavailable.
    """
    from backend.services.audit import write_audit
    from backend.models.audit import AuditAction

    # Write audit before calling Gemini
    write_audit(
        action=AuditAction.AI_DIAGNOSIS_REQUESTED,
        stage="diagnosis",
        details={"reason": event.reason, "gateway_message": event.gateway_message},
    )

    try:
        from backend.providers.gemini import GeminiClient
        client = GeminiClient()
        result = client.diagnose_failure(event)
        logger.info("Gemini diagnosis: %s (confidence=%.2f)", result.bucket, result.confidence)

        write_audit(
            action=AuditAction.DIAGNOSIS_COMPLETED,
            stage="diagnosis",
            details={
                "bucket": result.bucket,
                "confidence": result.confidence,
                "method": "gemini",
                "prompt_version": result.prompt_version,
            },
        )
        return result

    except Exception as exc:
        logger.error("Gemini diagnosis failed: %s", exc)
        write_audit(
            action=AuditAction.AI_DIAGNOSIS_FAILED,
            stage="diagnosis",
            details={"error": str(exc), "reason": event.reason},
        )
        return _fallback_diagnose(event)


def _fallback_diagnose(event: NormalizedRevenueEvent) -> DiagnosisResult:
    """
    Fallback when Gemini is unavailable.
    Uses FALLBACK_CODES if available; otherwise returns unknown → QUEUE_FOR_REVIEW.
    """
    from backend.services.audit import write_audit
    from backend.models.audit import AuditAction

    reason = event.reason.upper()
    if reason in FALLBACK_CODES:
        bucket, confidence = FALLBACK_CODES[reason]
        write_audit(
            action=AuditAction.AI_DIAGNOSIS_FALLBACK,
            stage="diagnosis",
            details={"reason": reason, "fallback_bucket": bucket},
        )
        return DiagnosisResult(
            bucket=bucket,
            confidence=confidence,
            method=DiagnosisMethod.FALLBACK,
            explanation=f"Gemini unavailable. Fallback mapping applied for '{reason}'.",
        )

    # No fallback available → return unknown with low confidence → policy → QUEUE_FOR_REVIEW
    write_audit(
        action=AuditAction.AI_DIAGNOSIS_FALLBACK,
        stage="diagnosis",
        details={"reason": reason, "fallback_bucket": "unknown", "gemini_unavailable": True},
    )
    return DiagnosisResult(
        bucket=DiagnosisBucket.UNKNOWN,
        confidence=0.30,
        method=DiagnosisMethod.FALLBACK,
        explanation="Gemini unavailable and no deterministic fallback. Case sent to review.",
    )
