"""
RevGuard — Pydantic models for Customer.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Customer(BaseModel):
    customer_id: str
    merchant_id: str
    name: str
    phone: str = ""
    email: str = ""
    language_pref: str = "english"  # english | hindi | hinglish
    whatsapp_opt_in: bool = True
    created_at: Optional[datetime] = None
