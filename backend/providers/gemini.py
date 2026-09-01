"""
RevGuard — Gemini AI Provider.

Three functions:
1. diagnose_failure(event) → DiagnosisResult
2. generate_recovery_message(case, customer, payment_link_url) → str (message text)
3. extract_reply_intent(raw_message, language) → CustomerReplyLog

All three validate schema rigorously. Malformed output → fallback, never crash.
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timezone

from backend import config
from backend.models.event import NormalizedRevenueEvent
from backend.models.case import DiagnosisResult, DiagnosisBucket, DiagnosisMethod, RecoveryCase
from backend.models.action import CustomerReplyLog, ReplyIntent
from backend.models.customer import Customer

logger = logging.getLogger(__name__)

PROMPT_DIR = Path(__file__).parent.parent / "ai" / "prompts"


class GeminiError(Exception):
    pass


class GeminiClient:
    """
    Wrapper around google-generativeai SDK.
    Uses structured JSON output where available.
    """

    def __init__(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.GEMINI_API_KEY)
            self._genai = genai
            self._model = genai.GenerativeModel(config.GEMINI_MODEL)
        except ImportError:
            raise GeminiError("google-generativeai package not installed. Run: pip install google-generativeai")

    def _load_prompt(self, filename: str) -> str:
        path = PROMPT_DIR / filename
        if not path.exists():
            raise GeminiError(f"Prompt file not found: {path}")
        return path.read_text(encoding="utf-8")

    def _call(self, system_prompt: str, user_content: str) -> str:
        """Make a Gemini API call and return raw text response."""
        try:
            response = self._model.generate_content(
                [
                    {"role": "user", "parts": [f"{system_prompt}\n\n---\nInput:\n{user_content}"]},
                ],
                generation_config={"response_mime_type": "application/json"},
            )
            return response.text
        except Exception as exc:
            raise GeminiError(f"Gemini API call failed: {exc}") from exc

    # ─── Prompt A: Failure Diagnosis ──────────────────────────────

    def diagnose_failure(self, event: NormalizedRevenueEvent) -> DiagnosisResult:
        """
        Classify an ambiguous failure into one of the approved buckets.
        Raises GeminiError on network/API failure (caller handles fallback).
        Raises ValueError on schema validation failure.
        """
        system_prompt = self._load_prompt("diagnose_failure_v1.md")
        user_content = json.dumps({
            "failure_code": event.reason,
            "gateway_message": event.gateway_message,
            "payment_method": "upi_autopay",
            "attempt_count": event.attempt_count,
        })

        raw = self._call(system_prompt, user_content)

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Gemini returned non-JSON: {raw[:200]}") from exc

        return self._validate_diagnosis_response(parsed)

    def _validate_diagnosis_response(self, parsed: dict) -> DiagnosisResult:
        """Validate and convert Gemini's diagnosis response."""
        allowed_buckets = {b.value for b in DiagnosisBucket}

        bucket = parsed.get("bucket", "").lower()
        if bucket not in allowed_buckets:
            raise ValueError(f"Invalid bucket from Gemini: '{bucket}'. Allowed: {allowed_buckets}")

        confidence = parsed.get("confidence")
        if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
            raise ValueError(f"Invalid confidence: {confidence}")

        evidence_summary = parsed.get("evidence_summary", "")
        if not evidence_summary or len(evidence_summary) > 1000:
            raise ValueError(f"Invalid evidence_summary length: {len(evidence_summary)}")

        return DiagnosisResult(
            bucket=DiagnosisBucket(bucket),
            confidence=float(confidence),
            method=DiagnosisMethod.GEMINI,
            explanation=evidence_summary,
            evidence_summary=evidence_summary,
            uncertainty=parsed.get("uncertainty", ""),
            prompt_version="diagnose_failure_v1",
            model_id=config.GEMINI_MODEL,
        )

    # ─── Prompt B: Recovery Message ────────────────────────────────

    def generate_recovery_message(
        self,
        case: RecoveryCase,
        customer: Customer,
        payment_link_url: str,
        merchant_name: str = "DemoMerchant",
    ) -> dict:
        """
        Generate a customer-facing recovery message.
        Returns dict with language, message, tone, contains_factual_claims_only.
        """
        system_prompt = self._load_prompt("recovery_message_v1.md")
        amount_rupees = case.amount / 100
        bucket = case.diagnosis.bucket if case.diagnosis else "unknown"

        user_content = json.dumps({
            "customer_name": customer.name,
            "amount_rupees": amount_rupees,
            "language_pref": customer.language_pref,
            "failure_bucket": bucket,
            "recovery_method": "payment_link",
            "payment_link": payment_link_url,
            "merchant_name": merchant_name,
        })

        raw = self._call(system_prompt, user_content)

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Gemini returned non-JSON for recovery message: {raw[:200]}") from exc

        return self._validate_message_response(parsed)

    def _validate_message_response(self, parsed: dict) -> dict:
        """Validate Gemini's recovery message response."""
        message = parsed.get("message", "")
        if not message or len(message) > 500:
            raise ValueError(f"Message out of bounds: length={len(message)}")

        language = parsed.get("language", "english")
        tone = parsed.get("tone", "polite")

        return {
            "language": language,
            "message": message,
            "tone": tone,
            "contains_factual_claims_only": parsed.get("contains_factual_claims_only", True),
            "prompt_version": "recovery_message_v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ─── Prompt C: Reply Intent ────────────────────────────────────

    def extract_reply_intent(
        self,
        raw_message: str,
        language: str = "english",
        current_date: str = "",
    ) -> dict:
        """
        Extract structured intent from a customer reply.
        Returns dict with intent, promised_date, confidence.
        """
        from datetime import date
        system_prompt = self._load_prompt("reply_intent_v1.md")
        user_content = json.dumps({
            "message": raw_message,
            "current_date": current_date or date.today().isoformat(),
            "language": language,
        })

        raw = self._call(system_prompt, user_content)

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Gemini returned non-JSON for reply intent: {raw[:200]}") from exc

        return self._validate_intent_response(parsed)

    def _validate_intent_response(self, parsed: dict) -> dict:
        """Validate Gemini's reply intent response."""
        allowed_intents = {i.value for i in ReplyIntent}
        intent = parsed.get("intent", "OTHER")
        if intent not in allowed_intents:
            raise ValueError(f"Invalid intent: '{intent}'. Allowed: {allowed_intents}")

        confidence = parsed.get("confidence", 0.5)
        if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
            raise ValueError(f"Invalid confidence: {confidence}")

        return {
            "intent": intent,
            "promised_date": parsed.get("promised_date"),  # YYYY-MM-DD or null
            "confidence": float(confidence),
            "prompt_version": "reply_intent_v1",
        }
