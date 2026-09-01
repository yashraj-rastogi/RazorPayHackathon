"""
RevGuard — Pydantic models for NormalizedRevenueEvent and related input types.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class NormalizedRevenueEvent(BaseModel):
    event_id: str
    merchant_id: str
    customer_id: str
    subscription_id: str
    revenue_type: str = "recurring_payment"
    amount: int = Field(..., description="Amount in paise (smallest currency unit)")
    currency: str = "INR"
    status: str = "failed"
    reason: str
    gateway_message: str = ""
    attempt_count: int = 1
    occurred_at: Optional[datetime] = None
    metadata: Optional[dict] = None
