# RevGuard — Engineering Log

## Day 1 (Sep 2, 2026)

### 09:00 — Project setup
- Confirmed tech stack: FastAPI backend, Vite + React frontend, Firebase Firestore, Razorpay Test Mode, Gemini API
- Confirmed messaging provider: Mock (with Twilio abstraction ready)
- Confirmed recovery action: Razorpay Payment Link via POST /v1/payment_links
- Created project structure

### Decisions Made
- Policy thresholds centralized in `backend/config.py` — NOT scattered
- AI (Gemini) only called for unknown/ambiguous failure codes
- All amounts stored in paise; displayed in rupees
- Audit log is strictly append-only — no updates

### Risks Noted
- Razorpay webhook requires public URL → plan to use ngrok during demo
- Firestore compound index needed for `provider_reference` field
- Gemini structured output validation must be strict at the backend boundary
