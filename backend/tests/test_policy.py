"""
RevGuard — Unit Tests: Policy Engine.

Tests all policy branches. These are the most critical tests in the codebase.
Run: pytest backend/tests/test_policy.py -v
"""

import pytest
from unittest.mock import patch

# Temporarily patch Firestore to avoid real DB calls during unit tests
import sys
from unittest.mock import MagicMock

# Patch firestore before imports
sys.modules['firebase_admin'] = MagicMock()
sys.modules['firebase_admin.credentials'] = MagicMock()
sys.modules['firebase_admin.firestore'] = MagicMock()

from backend.models.case import (
    RecoveryCase, DiagnosisResult, DiagnosisBucket, DiagnosisMethod, PolicyDecisionType
)
from backend.services import policy as policy_service
from backend import config


def make_case(
    amount: int = 49900,       # Rs.499
    bucket: str = DiagnosisBucket.TEMPORARY_FAILURE,
    confidence: float = 0.97,
    method: str = DiagnosisMethod.DETERMINISTIC,
) -> RecoveryCase:
    """Helper: create a minimal RecoveryCase for policy testing."""
    return RecoveryCase(
        case_id="test_case_001",
        event_id="evt_001",
        merchant_id="m_001",
        customer_id="c_001",
        amount=amount,
        diagnosis=DiagnosisResult(
            bucket=bucket,
            confidence=confidence,
            method=method,
            explanation="test",
        ),
    )


# ─── BLOCKED paths ─────────────────────────────────────────────────

class TestBlockedCases:
    def test_payment_already_succeeded(self):
        case = make_case()
        result = policy_service.evaluate(case, payment_already_succeeded=True)
        assert result.decision == PolicyDecisionType.BLOCKED
        assert result.block_reason == "PAYMENT_ALREADY_SUCCEEDED"

    def test_mandate_inactive(self):
        case = make_case()
        result = policy_service.evaluate(case, mandate_is_inactive=True)
        assert result.decision == PolicyDecisionType.BLOCKED
        assert result.block_reason == "MANDATE_INACTIVE"

    def test_customer_opted_out(self):
        case = make_case()
        result = policy_service.evaluate(case, customer_opted_out=True)
        assert result.decision == PolicyDecisionType.BLOCKED
        assert result.block_reason == "CUSTOMER_OPTED_OUT"

    def test_mandate_inactive_bucket(self):
        """Mandate inactive bucket → BLOCKED even without explicit flag."""
        case = make_case(bucket=DiagnosisBucket.MANDATE_INACTIVE, confidence=0.99)
        result = policy_service.evaluate(case)
        assert result.decision == PolicyDecisionType.BLOCKED
        assert result.block_reason == "NON_RECOVERABLE_BUCKET"

    def test_blocked_checks_before_review(self):
        """BLOCKED checks take precedence over QUEUE_FOR_REVIEW checks."""
        # Low confidence + opted out → should be BLOCKED, not QUEUE_FOR_REVIEW
        case = make_case(confidence=0.50)  # Low confidence
        result = policy_service.evaluate(case, customer_opted_out=True)
        assert result.decision == PolicyDecisionType.BLOCKED

    def test_no_diagnosis(self):
        """No diagnosis → QUEUE_FOR_REVIEW."""
        case = RecoveryCase(
            case_id="test", event_id="evt", merchant_id="m", customer_id="c", amount=49900
        )
        case.diagnosis = None
        result = policy_service.evaluate(case)
        assert result.decision == PolicyDecisionType.QUEUE_FOR_REVIEW


# ─── QUEUE_FOR_REVIEW paths ────────────────────────────────────────

class TestQueueForReview:
    def test_low_confidence(self):
        """Confidence below threshold → QUEUE_FOR_REVIEW."""
        case = make_case(confidence=config.POLICY_MIN_CONFIDENCE_AUTO - 0.01)
        result = policy_service.evaluate(case)
        assert result.decision == PolicyDecisionType.QUEUE_FOR_REVIEW
        assert any("confidence" in r.lower() for r in result.reasons)

    def test_confidence_at_threshold_is_auto(self):
        """Confidence exactly at threshold → AUTO (not review)."""
        case = make_case(confidence=config.POLICY_MIN_CONFIDENCE_AUTO)
        result = policy_service.evaluate(case)
        assert result.decision == PolicyDecisionType.AUTO

    def test_amount_above_threshold(self):
        """Amount >= Rs.10,000 (1,000,000 paise) → QUEUE_FOR_REVIEW."""
        case = make_case(amount=config.POLICY_MAX_AMOUNT_AUTO)
        result = policy_service.evaluate(case)
        assert result.decision == PolicyDecisionType.QUEUE_FOR_REVIEW
        assert any("amount" in r.lower() for r in result.reasons)

    def test_amount_below_threshold_is_auto(self):
        """Amount just below threshold → AUTO."""
        case = make_case(amount=config.POLICY_MAX_AMOUNT_AUTO - 100)
        result = policy_service.evaluate(case)
        assert result.decision == PolicyDecisionType.AUTO

    def test_retry_limit_reached(self):
        """attempt_count >= POLICY_MAX_RETRY_AUTO → QUEUE_FOR_REVIEW."""
        case = make_case()
        result = policy_service.evaluate(case, attempt_count=config.POLICY_MAX_RETRY_AUTO)
        assert result.decision == PolicyDecisionType.QUEUE_FOR_REVIEW
        assert any("attempt" in r.lower() for r in result.reasons)

    def test_retry_below_limit_is_auto(self):
        """attempt_count = POLICY_MAX_RETRY_AUTO - 1 → AUTO."""
        case = make_case()
        result = policy_service.evaluate(case, attempt_count=config.POLICY_MAX_RETRY_AUTO - 1)
        assert result.decision == PolicyDecisionType.AUTO


# ─── AUTO path ─────────────────────────────────────────────────────

class TestAutoApproval:
    def test_basic_auto_case(self):
        """Standard low-value, high-confidence, low-retry case → AUTO."""
        case = make_case(
            amount=49900,         # Rs.499 — well below threshold
            confidence=0.97,
            bucket=DiagnosisBucket.TEMPORARY_FAILURE,
        )
        result = policy_service.evaluate(case, attempt_count=1)
        assert result.decision == PolicyDecisionType.AUTO
        assert len(result.reasons) >= 3

    def test_auto_includes_reasons(self):
        """AUTO decision must include reasons explaining why."""
        case = make_case()
        result = policy_service.evaluate(case)
        assert result.decision == PolicyDecisionType.AUTO
        assert result.reasons  # non-empty

    def test_auto_has_policy_version(self):
        """AUTO decision must include policy_version."""
        case = make_case()
        result = policy_service.evaluate(case)
        assert result.decision == PolicyDecisionType.AUTO
        assert result.policy_version  # non-empty


# ─── Edge cases ────────────────────────────────────────────────────

class TestEdgeCases:
    def test_amount_exactly_one_rupee(self):
        """Minimum meaningful amount → AUTO."""
        case = make_case(amount=100)  # Rs.1
        result = policy_service.evaluate(case)
        assert result.decision == PolicyDecisionType.AUTO

    def test_gemini_method_below_confidence(self):
        """Gemini result below threshold → QUEUE_FOR_REVIEW."""
        case = make_case(confidence=0.60, method=DiagnosisMethod.GEMINI)
        result = policy_service.evaluate(case)
        assert result.decision == PolicyDecisionType.QUEUE_FOR_REVIEW

    def test_payment_succeeded_overrides_everything(self):
        """payment_already_succeeded = True → BLOCKED regardless of amount/confidence."""
        case = make_case(amount=100, confidence=0.99)  # Would be AUTO
        result = policy_service.evaluate(case, payment_already_succeeded=True)
        assert result.decision == PolicyDecisionType.BLOCKED

    def test_insufficient_funds_auto_path(self):
        """Insufficient funds with sufficient confidence → AUTO."""
        case = make_case(
            bucket=DiagnosisBucket.INSUFFICIENT_FUNDS,
            confidence=0.99,
            amount=49900,
        )
        result = policy_service.evaluate(case)
        assert result.decision == PolicyDecisionType.AUTO

    def test_unknown_bucket_low_confidence(self):
        """Unknown bucket + Gemini fallback confidence → QUEUE_FOR_REVIEW."""
        case = make_case(
            bucket=DiagnosisBucket.UNKNOWN,
            confidence=0.30,
            method=DiagnosisMethod.FALLBACK,
        )
        result = policy_service.evaluate(case)
        assert result.decision == PolicyDecisionType.QUEUE_FOR_REVIEW
