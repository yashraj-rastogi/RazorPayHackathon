"""
RevGuard — Twilio WhatsApp Messaging Provider.

Dispatches synthesized customer recovery messages via Twilio WhatsApp API.
Uses direct REST endpoint with HTTP Basic Auth (no extra SDK required).
"""

import os
import logging
import requests
from backend.db.firestore import set_document, now_utc

logger = logging.getLogger(__name__)


class DeliveryResult:
    def __init__(self, status: str, provider_reference: str, provider: str = "twilio"):
        self.status = status
        self.provider_reference = provider_reference
        self.provider = provider


class TwilioMessagingProvider:
    def __init__(self):
        from backend import config
        self.account_sid = config.TWILIO_ACCOUNT_SID
        self.auth_token = config.TWILIO_AUTH_TOKEN
        self.from_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        self.test_phone_override = os.getenv("TWILIO_TEST_PHONE_OVERRIDE", "")

        if not self.account_sid or not self.auth_token:
            logger.warning("Twilio credentials missing. Messages will fail unless configured.")

    def send(self, phone: str, message: str, case_id: str = "") -> DeliveryResult:
        """
        Send a WhatsApp message via Twilio REST API.
        Recipient number must be formatted in E.164 (e.g., +919876543210).
        """
        target_phone = self.test_phone_override if self.test_phone_override else phone

        # Format with whatsapp: prefix if not present
        to_address = target_phone if target_phone.startswith("whatsapp:") else f"whatsapp:{target_phone}"
        from_address = self.from_number if self.from_number.startswith("whatsapp:") else f"whatsapp:{self.from_number}"

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        payload = {
            "From": from_address,
            "To": to_address,
            "Body": message,
        }

        try:
            logger.info("Dispatching Twilio WhatsApp message to %s (case: %s)", to_address, case_id)
            response = requests.post(
                url,
                data=payload,
                auth=(self.account_sid, self.auth_token),
                timeout=10,
            )

            res_data = response.json() if response.content else {}

            if response.status_code not in (200, 201):
                error_msg = res_data.get("message", response.text)
                logger.error("Twilio WhatsApp dispatch failed (%s): %s", response.status_code, error_msg)
                return DeliveryResult(status="failed", provider_reference=error_msg, provider="twilio")

            sid = res_data.get("sid", "unknown")
            logger.info("Twilio WhatsApp message sent successfully! SID: %s", sid)

            # Log to Firestore for transparency
            log_doc = {
                "message_id": sid,
                "phone": to_address,
                "message": message,
                "case_id": case_id,
                "provider": "twilio",
                "sent_at": now_utc().isoformat(),
                "status": res_data.get("status", "sent"),
            }
            try:
                set_document("dispatched_messages", sid, log_doc)
            except Exception:
                pass

            return DeliveryResult(status="delivered", provider_reference=sid, provider="twilio")

        except Exception as exc:
            logger.error("Twilio request exception: %s", exc)
            return DeliveryResult(status="failed", provider_reference=str(exc), provider="twilio")
