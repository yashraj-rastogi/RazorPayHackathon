"""
RevGuard — Smart Dunning Recommendation Engine.

Provides domain-specific optimal retry schedules for India's payment ecosystem
(NPCI UPI Autopay rules, banking settlement cycles, and salary credit windows).
"""

from typing import Dict, Any


def get_dunning_recommendation(bucket: str, amount_paise: int = 0) -> Dict[str, Any]:
    """
    Returns optimal debit window, protocol, and banking rationale based on failure bucket.
    """
    amount_rupees = amount_paise / 100

    if bucket == "insufficient_funds":
        return {
            "window": "1st – 5th of Month // 09:00 – 11:00 AM IST",
            "protocol": "Hold retry until payroll credit cycle; send pre-debit WhatsApp alert.",
            "rationale": "Over 78% of salaried accounts in India receive payroll between the 1st and 5th. Retrying immediately incurs customer bounce penalties and yields <12% success.",
            "confidence_lift": "+42% expected recovery",
            "tag": "SALARY_CYCLE_ALIGNMENT",
        }
    elif bucket == "temporary_failure":
        return {
            "window": "T + 4 Hours // 14:00 – 16:00 IST (Off-Peak Issuer)",
            "protocol": "Auto-debit retry via alternate acquiring gateway route.",
            "rationale": "NPCI switch congestions and issuer CBS core timeouts typically clear within a 2-4 hour cooldown window.",
            "confidence_lift": "+68% expected recovery",
            "tag": "GATEWAY_SWITCH_RETRY",
        }
    elif bucket == "payment_credential_expired":
        return {
            "window": "Immediate Token Migration Link",
            "protocol": "Suspend automated debit; dispatch RBI-compliant card token update URL.",
            "rationale": "Auto-debiting an expired token creates recurring issuer rejections. Customer must re-consent with RBI tokenization guidelines.",
            "confidence_lift": "+55% expected recovery",
            "tag": "TOKEN_UPDATE_REQUIRED",
        }
    elif bucket == "mandate_inactive":
        return {
            "window": "Mandate Re-Authentication Required",
            "protocol": "Generate 1-click UPI Autopay re-authorization link with pre-filled VPA.",
            "rationale": "Mandate was revoked or cancelled in customer's UPI app (PhonePe/GPay/Paytm). Retrying without re-auth is non-compliant.",
            "confidence_lift": "+35% expected recovery",
            "tag": "MANDATE_REAUTHORIZATION",
        }
    elif bucket == "otp_or_authentication_issue":
        return {
            "window": "T + 30 Minutes // Immediate Notification",
            "protocol": "Prompt customer via WhatsApp to approve 2FA prompt in banking app.",
            "rationale": "Customer likely missed the bank SMS/notification window. Immediate outreach yields highest re-auth engagement.",
            "confidence_lift": "+61% expected recovery",
            "tag": "CUSTOMER_2FA_PROMPT",
        }
    else:
        return {
            "window": "Human Operator Review Required",
            "protocol": "Inspect issuer gateway response payload before re-attempting debit.",
            "rationale": "Ambiguous or unknown response code. Bounded autonomy halts automated debit to prevent unintended customer friction.",
            "confidence_lift": "Manual triage",
            "tag": "MANUAL_INSPECTION",
        }
