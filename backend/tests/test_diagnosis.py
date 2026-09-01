"""
RevGuard — Unit Tests: Diagnosis Service.

Tests deterministic → Gemini routing, fallback behavior, and schema validation.
Run: pytest backend/tests/test_diagnosis.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
import sys

# Patch firebase before imports
sys.modules['firebase_admin'] = MagicMock()
sys.modules['firebase_admin.credentials'] = MagicMock()
sys.modules['firebase_admin.firestore'] = MagicMock()

from backend.models.event import NormalizedRevenueEvent
from backend.models.case import DiagnosisBucket, DiagnosisMethod
from backend.services import diagnosis as diagnosis_service


def make_event(reason: str = "BANK_TIMEOUT", gateway_message: str = "Timeout") -> NormalizedRevenueEvent:
    return NormalizedRevenueEvent(
        event_id="evt_test",
        merchant_id="m_001",
        customer_id="c_001",
        subscription_id="sub_001",
        amount=49900,
        reason=reason,
        gateway_message=gateway_message,
        attempt_count=1,
    )


# ─── Deterministic mapping ─────────────────────────────────────────

class TestDeterministicMapping:
    def test_bank_timeout_maps_correctly(self):
        event = make_event("BANK_TIMEOUT")
        with patch("backend.services.audit.write_audit"):
            result = diagnosis_service.diagnose(event)
        assert result.bucket == DiagnosisBucket.TEMPORARY_FAILURE
        assert result.method == DiagnosisMethod.DETERMINISTIC
        assert result.confidence >= 0.95

    def test_insufficient_funds_maps_correctly(self):
        event = make_event("INSUFFICIENT_FUNDS")
        with patch("backend.services.audit.write_audit"):
            result = diagnosis_service.diagnose(event)
        assert result.bucket == DiagnosisBucket.INSUFFICIENT_FUNDS
        assert result.method == DiagnosisMethod.DETERMINISTIC
        assert result.confidence >= 0.97

    def test_card_expired_maps_correctly(self):
        event = make_event("CARD_EXPIRED")
        with patch("backend.services.audit.write_audit"):
            result = diagnosis_service.diagnose(event)
        assert result.bucket == DiagnosisBucket.PAYMENT_CREDENTIAL_EXPIRED
        assert result.method == DiagnosisMethod.DETERMINISTIC

    def test_mandate_cancelled_maps_correctly(self):
        event = make_event("MANDATE_CANCELLED")
        with patch("backend.services.audit.write_audit"):
            result = diagnosis_service.diagnose(event)
        assert result.bucket == DiagnosisBucket.MANDATE_INACTIVE
        assert result.method == DiagnosisMethod.DETERMINISTIC

    def test_otp_failed_maps_correctly(self):
        event = make_event("OTP_FAILED")
        with patch("backend.services.audit.write_audit"):
            result = diagnosis_service.diagnose(event)
        assert result.bucket == DiagnosisBucket.OTP_OR_AUTHENTICATION_ISSUE
        assert result.method == DiagnosisMethod.DETERMINISTIC

    def test_case_insensitive_reason(self):
        """Reason codes should match case-insensitively."""
        event = make_event("bank_timeout")
        with patch("backend.services.audit.write_audit"):
            result = diagnosis_service.diagnose(event)
        assert result.bucket == DiagnosisBucket.TEMPORARY_FAILURE

    def test_deterministic_does_not_call_gemini(self):
        """Known codes must NOT trigger Gemini calls."""
        event = make_event("BANK_TIMEOUT")
        with patch("backend.services.audit.write_audit"):
            with patch("backend.providers.gemini.GeminiClient") as mock_gemini:
                diagnosis_service.diagnose(event)
                mock_gemini.assert_not_called()


# ─── Gemini routing ────────────────────────────────────────────────

class TestGeminiRouting:
    def test_unknown_code_calls_gemini(self):
        """Unknown reason code → Gemini is called."""
        event = make_event("UNKNOWN_GATEWAY_ERROR", "Unexpected issuer response")
        mock_result = MagicMock()
        mock_result.bucket = DiagnosisBucket.TEMPORARY_FAILURE
        mock_result.confidence = 0.82
        mock_result.method = DiagnosisMethod.GEMINI
        mock_result.explanation = "Seems like a temporary issue"
        mock_result.prompt_version = "diagnose_failure_v1"

        with patch("backend.services.audit.write_audit"):
            with patch("backend.providers.gemini.GeminiClient") as MockGemini:
                mock_client = MockGemini.return_value
                mock_client.diagnose_failure.return_value = mock_result
                result = diagnosis_service._gemini_diagnose(event)

        assert result.method == DiagnosisMethod.GEMINI

    def test_gemini_timeout_triggers_fallback(self):
        """Gemini timeout → fallback to deterministic or QUEUE_FOR_REVIEW."""
        event = make_event("UNKNOWN_GATEWAY_ERROR", "Ambiguous error")
        with patch("backend.services.audit.write_audit"):
            with patch("backend.providers.gemini.GeminiClient") as MockGemini:
                MockGemini.side_effect = Exception("Connection timeout")
                result = diagnosis_service._gemini_diagnose(event)

        assert result.method == DiagnosisMethod.FALLBACK
        assert result.confidence < 0.85  # Should be low → QUEUE_FOR_REVIEW

    def test_gemini_schema_error_triggers_fallback(self):
        """Gemini returns malformed schema → fallback, no crash."""
        event = make_event("UNKNOWN_GATEWAY_ERROR", "Weird message")
        with patch("backend.services.audit.write_audit"):
            with patch("backend.providers.gemini.GeminiClient") as MockGemini:
                mock_client = MockGemini.return_value
                mock_client.diagnose_failure.side_effect = ValueError("Invalid bucket 'xyz'")
                result = diagnosis_service._gemini_diagnose(event)

        assert result.method == DiagnosisMethod.FALLBACK

    def test_fallback_to_unknown_when_no_deterministic(self):
        """Unknown code with no fallback → bucket=unknown, low confidence."""
        event = make_event("TOTALLY_NEW_CODE_XYZ", "Never seen this before")
        with patch("backend.services.audit.write_audit"):
            with patch("backend.providers.gemini.GeminiClient") as MockGemini:
                MockGemini.side_effect = Exception("Gemini unavailable")
                result = diagnosis_service._gemini_diagnose(event)

        assert result.bucket == DiagnosisBucket.UNKNOWN
        assert result.method == DiagnosisMethod.FALLBACK
        assert result.confidence < 0.50


# ─── Schema validation in Gemini client ────────────────────────────

class TestGeminiSchemaValidation:
    def test_invalid_bucket_rejected(self):
        from backend.providers.gemini import GeminiClient
        client = GeminiClient.__new__(GeminiClient)  # Don't call __init__
        with pytest.raises(ValueError, match="Invalid bucket"):
            client._validate_diagnosis_response({"bucket": "made_up_bucket", "confidence": 0.9, "evidence_summary": "x"})

    def test_confidence_out_of_range_rejected(self):
        from backend.providers.gemini import GeminiClient
        client = GeminiClient.__new__(GeminiClient)
        with pytest.raises(ValueError, match="confidence"):
            client._validate_diagnosis_response({"bucket": "temporary_failure", "confidence": 1.5, "evidence_summary": "x"})

    def test_empty_evidence_rejected(self):
        from backend.providers.gemini import GeminiClient
        client = GeminiClient.__new__(GeminiClient)
        with pytest.raises(ValueError):
            client._validate_diagnosis_response({"bucket": "temporary_failure", "confidence": 0.9, "evidence_summary": ""})

    def test_valid_response_accepted(self):
        from backend.providers.gemini import GeminiClient
        client = GeminiClient.__new__(GeminiClient)
        result = client._validate_diagnosis_response({
            "bucket": "temporary_failure",
            "confidence": 0.91,
            "evidence_summary": "The message describes an issuer-side failure.",
            "uncertainty": "No definitive code.",
        })
        assert result.bucket == DiagnosisBucket.TEMPORARY_FAILURE
        assert result.confidence == 0.91
        assert result.method == DiagnosisMethod.GEMINI
