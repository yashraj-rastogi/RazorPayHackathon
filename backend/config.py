"""
RevGuard — Central Configuration
All policy thresholds and environment variables are loaded here.
Never scatter thresholds across service code.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── External Services ───────────────────────────────────────────
RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "")

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

FIRESTORE_PROJECT_ID: str = os.getenv("FIRESTORE_PROJECT_ID", "")

MESSAGING_PROVIDER: str = os.getenv("MESSAGING_PROVIDER", "mock")
TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")

# ─── Policy Thresholds ───────────────────────────────────────────
# Amount above which AUTO is forbidden; cases go to QUEUE_FOR_REVIEW
POLICY_MAX_AMOUNT_AUTO: int = int(os.getenv("POLICY_MAX_AMOUNT_AUTO", "1000000"))  # paise = Rs.10,000

# Minimum AI confidence required for AUTO action
POLICY_MIN_CONFIDENCE_AUTO: float = float(os.getenv("POLICY_MIN_CONFIDENCE_AUTO", "0.85"))

# Max retry attempts before forcing QUEUE_FOR_REVIEW
POLICY_MAX_RETRY_AUTO: int = int(os.getenv("POLICY_MAX_RETRY_AUTO", "3"))

# Policy engine version — bump when rules change
POLICY_VERSION: str = "v1"

# ─── App Settings ────────────────────────────────────────────────
APP_ENV: str = os.getenv("APP_ENV", "development")
CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
