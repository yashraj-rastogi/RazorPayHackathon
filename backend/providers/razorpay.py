"""
RevGuard — Razorpay Payment Provider.

Uses only endpoints verified in Test Mode:
  POST /v1/payment_links  (create recovery payment link)
  GET  /v1/payment_links/{id}  (check payment link status)

WARNING: Do NOT invent a "retry subscription payment" endpoint.
Razorpay Test Mode does not expose a generic recurring-charge retry API.
"""

import hashlib
import hmac
import logging
from typing import Optional

from backend import config

logger = logging.getLogger(__name__)


class PaymentLinkResult:
    def __init__(self, provider_reference: str, short_url: str, status: str):
        self.provider_reference = provider_reference
        self.short_url = short_url
        self.status = status


class RazorpayProvider:
    """
    Concrete Razorpay implementation.
    All amounts expected in paise.
    """

    BASE_URL = "https://api.razorpay.com/v1"

    def __init__(self):
        self.key_id = config.RAZORPAY_KEY_ID
        self.key_secret = config.RAZORPAY_KEY_SECRET
        if not self.key_id or not self.key_secret:
            logger.warning("Razorpay credentials not configured. Calls will fail.")

    def _get_auth(self):
        import base64
        creds = f"{self.key_id}:{self.key_secret}"
        return base64.b64encode(creds.encode()).decode()

    def create_recovery_payment_link(
        self,
        case_id: str,
        amount: int,
        customer_name: str,
        customer_email: str,
        customer_phone: str,
        description: str,
        idempotency_key: str,
    ) -> PaymentLinkResult:
        """
        Create a Razorpay Standard Payment Link.
        Returns PaymentLinkResult with plink_xxx reference and short URL.

        Raises:
            requests.Timeout — caller should mark action UNKNOWN and verify
            requests.HTTPError — caller should mark action FAILED
        """
        import requests

        payload = {
            "amount": amount,
            "currency": "INR",
            "accept_partial": False,
            "description": description,
            "customer": {
                "name": customer_name,
                "email": customer_email,
                "contact": customer_phone,
            },
            "notify": {
                "sms": False,   # RevGuard handles messaging
                "email": False,
            },
            "reminder_enable": False,
            "notes": {
                "revguard_case_id": case_id,
                "idempotency_key": idempotency_key,
            },
            "callback_url": "",
            "callback_method": "get",
        }

        headers = {
            "Authorization": f"Basic {self._get_auth()}",
            "Content-Type": "application/json",
            "X-Razorpay-Idempotency-Key": idempotency_key,
        }

        response = requests.post(
            f"{self.BASE_URL}/payment_links",
            json=payload,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        return PaymentLinkResult(
            provider_reference=data["id"],
            short_url=data.get("short_url", ""),
            status=data.get("status", "created"),
        )

    def get_payment_link_status(self, provider_reference: str) -> str:
        """
        Verify the current state of a payment link.
        Returns status string: 'created' | 'paid' | 'cancelled' | 'expired'
        Used for idempotency verification after timeout.
        """
        import requests

        headers = {"Authorization": f"Basic {self._get_auth()}"}
        response = requests.get(
            f"{self.BASE_URL}/payment_links/{provider_reference}",
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("status", "unknown")

    def verify_webhook_signature(
        self,
        payload_body: bytes,
        signature: str,
        webhook_secret: str,
    ) -> bool:
        """
        Verify Razorpay webhook HMAC-SHA256 signature.
        payload_body = raw request bytes, NOT parsed JSON.
        """
        expected = hmac.new(
            webhook_secret.encode(),
            payload_body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
