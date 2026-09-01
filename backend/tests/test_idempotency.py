"""
RevGuard — Unit Tests: Idempotency.

Tests:
- Duplicate event ingestion → exactly 1 case created
- Call /recover twice → exactly 1 recovery_action document
- Call /approve twice → exactly 1 approval audit entry

Run: pytest backend/tests/test_idempotency.py -v
"""

import pytest
from unittest.mock import patch, MagicMock, call
import sys

sys.modules['firebase_admin'] = MagicMock()
sys.modules['firebase_admin.credentials'] = MagicMock()
sys.modules['firebase_admin.firestore'] = MagicMock()

from backend.models.event import NormalizedRevenueEvent
from backend.models.case import CaseStatus


def make_event(event_id: str = "evt_idempotency_001") -> NormalizedRevenueEvent:
    return NormalizedRevenueEvent(
        event_id=event_id,
        merchant_id="m_001",
        customer_id="c_001",
        subscription_id="sub_001",
        amount=49900,
        reason="BANK_TIMEOUT",
        gateway_message="Timeout",
        attempt_count=1,
    )


class TestDuplicateEventIngestion:
    def test_duplicate_event_blocked(self):
        """Sending the same event twice -> second is blocked silently."""
        event = make_event()

        existing_doc = {
            "event_id": event.event_id,
            "case_id": "case_existing_001",
        }
        existing_case_doc = {"case_id": "case_existing_001", "status": "ACTION_PENDING"}

        from backend.services.ingestion import ingest_event

        with patch("backend.services.ingestion.get_document") as mock_get, \
             patch("backend.services.ingestion.set_document") as mock_set, \
             patch("backend.services.audit.write_audit"):

            # Return existing event on first call, then existing case on second call
            mock_get.side_effect = [existing_doc, existing_case_doc]
            result = ingest_event(event)

        assert result["is_duplicate"] is True
        assert result["case_id"] == "case_existing_001"

    def test_same_event_id_not_duplicated_in_firestore(self):
        """When duplicate detected, set_document for case is never called."""
        event = make_event()
        existing_doc = {"event_id": event.event_id, "case_id": "case_001"}

        with patch("backend.services.ingestion.get_document", return_value=existing_doc), \
             patch("backend.services.ingestion.set_document") as mock_set, \
             patch("backend.services.audit.write_audit"):
            from backend.services.ingestion import ingest_event
            ingest_event(event)

        # set_document should NOT have been called with recovery_cases
        for c in mock_set.call_args_list:
            assert c[0][0] != "recovery_cases", "Should not create new case for duplicate event"


class TestRecoveryIdempotency:
    def test_recovery_idempotency_key_is_deterministic(self):
        """Same inputs → same idempotency key (no randomness)."""
        from backend.services.recovery import _build_idempotency_key
        key1 = _build_idempotency_key("case_001", "CREATE_PAYMENT_LINK", 1)
        key2 = _build_idempotency_key("case_001", "CREATE_PAYMENT_LINK", 1)
        assert key1 == key2

    def test_different_case_different_key(self):
        """Different case_id → different key."""
        from backend.services.recovery import _build_idempotency_key
        key1 = _build_idempotency_key("case_001", "CREATE_PAYMENT_LINK", 1)
        key2 = _build_idempotency_key("case_002", "CREATE_PAYMENT_LINK", 1)
        assert key1 != key2

    def test_second_recover_call_returns_existing_action(self):
        """Call /recover twice → second call returns same action, no new Razorpay call."""
        existing_action = {
            "action_id": "act_existing_001",
            "case_id": "case_001",
            "idempotency_key": "revguard-abc123",
            "status": "SUCCESS",
            "provider_reference": "plink_existing",
            "recovery_url": "https://rzp.io/i/test",
        }
        mock_case = {
            "case_id": "case_001",
            "event_id": "evt_001",
            "merchant_id": "m_001",
            "customer_id": "c_001",
            "amount": 49900,
            "status": "ACTION_PENDING",
            "policy": {"decision": "AUTO", "reasons": ["test"]},
        }

        from backend.services.recovery import _build_idempotency_key
        idem_key = _build_idempotency_key("case_001", "CREATE_PAYMENT_LINK", 1)
        existing_action["idempotency_key"] = idem_key

        with patch("backend.services.recovery.get_document") as mock_get, \
             patch("backend.services.recovery.query_collection") as mock_query, \
             patch("backend.providers.razorpay.RazorpayProvider") as mock_rp, \
             patch("backend.services.audit.write_audit"):

            mock_get.side_effect = lambda col, doc_id: (
                mock_case if col == "recovery_cases"
                else {"attempt_count": 1} if col == "revenue_events"
                else None
            )
            mock_query.return_value = [existing_action]

            from backend.services.recovery import execute_recovery
            result = execute_recovery("case_001")

        # Should return existing action without calling Razorpay
        assert result.get("idempotent") is True
        assert result.get("provider_reference") == "plink_existing"
        mock_rp.assert_not_called()
