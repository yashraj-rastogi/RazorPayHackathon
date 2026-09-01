"""
RevGuard — Mock Messaging Provider.

Logs messages to Firestore instead of sending real WhatsApp/SMS.
Interface is identical to a real Twilio provider so swapping is trivial.
"""

import uuid
import logging
from datetime import timezone, datetime

from backend.db.firestore import set_document, now_utc

logger = logging.getLogger(__name__)


class DeliveryResult:
    def __init__(self, status: str, provider_reference: str, provider: str = "mock"):
        self.status = status
        self.provider_reference = provider_reference
        self.provider = provider


class MockMessagingProvider:
    """
    Development/demo messaging provider.
    Stores all messages in Firestore `mock_messages` collection.
    """

    def send(self, phone: str, message: str, case_id: str = "") -> DeliveryResult:
        msg_id = f"mock_{uuid.uuid4().hex[:8]}"
        doc = {
            "message_id": msg_id,
            "phone": phone,
            "message": message,
            "case_id": case_id,
            "provider": "mock",
            "sent_at": now_utc().isoformat(),
            "status": "delivered",
        }
        try:
            set_document("mock_messages", msg_id, doc)
            logger.info("[MOCK MSG] → %s: %s...", phone, message[:60])
        except Exception as exc:
            logger.error("Failed to log mock message: %s", exc)

        return DeliveryResult(status="delivered", provider_reference=msg_id, provider="mock")


def get_messaging_provider():
    """
    Factory: returns the configured messaging provider.
    Swap to Twilio by setting MESSAGING_PROVIDER=twilio in .env
    """
    from backend import config
    if config.MESSAGING_PROVIDER == "twilio":
        try:
            from backend.providers.twilio_provider import TwilioMessagingProvider
            return TwilioMessagingProvider()
        except ImportError:
            logger.warning("Twilio provider not available; falling back to mock.")
    return MockMessagingProvider()
