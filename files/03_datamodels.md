# RevGuard — Data Models

## 1. Design principles

1. Keep the event schema generic.
2. Keep financial amounts integer-valued in the smallest currency unit.
3. Store all timestamps in UTC.
4. Never store API secrets in Firestore.
5. Treat audit records as append-only.
6. Make recovery actions idempotent.
7. Store model confidence separately from business policy decisions.

## 2. Collection overview

```text
merchants
customers
subscriptions
revenue_events
recovery_cases
recovery_actions
audit_logs
evaluation_runs
```

## 3. Merchant

```json
{
  "merchant_id": "m_001",
  "name": "DemoMerchant",
  "currency": "INR",
  "timezone": "Asia/Kolkata",
  "created_at": "timestamp"
}
```

## 4. Customer

```json
{
  "customer_id": "c_001",
  "merchant_id": "m_001",
  "name": "Rahul",
  "phone": "+91XXXXXXXXXX",
  "email": "demo@example.com",
  "language_pref": "hinglish",
  "whatsapp_opt_in": true,
  "created_at": "timestamp"
}
```

## 5. Subscription

```json
{
  "subscription_id": "sub_001",
  "merchant_id": "m_001",
  "customer_id": "c_001",
  "razorpay_subscription_id": "sub_xxx",
  "payment_method": "upi_autopay",
  "amount": 249900,
  "currency": "INR",
  "status": "active",
  "next_charge_at": "timestamp",
  "mandate_status": "active",
  "created_at": "timestamp"
}
```

Amounts use paise for INR.

## 6. Revenue Event

This is the canonical event model.

```json
{
  "event_id": "evt_001",
  "merchant_id": "m_001",
  "customer_id": "c_001",
  "subscription_id": "sub_001",
  "revenue_type": "recurring_payment",
  "amount": 249900,
  "currency": "INR",
  "status": "failed",
  "reason": "BANK_TIMEOUT",
  "gateway_message": "Issuer response unavailable",
  "attempt_count": 1,
  "occurred_at": "timestamp",
  "metadata": {
    "source": "synthetic"
  }
}
```

## 7. DiagnosisResult

```json
{
  "diagnosis_id": "diag_001",
  "event_id": "evt_001",
  "bucket": "temporary_failure",
  "confidence": 0.96,
  "method": "deterministic",
  "explanation": "BANK_TIMEOUT mapped to temporary failure",
  "created_at": "timestamp"
}
```

Allowed buckets:

```text
temporary_failure
insufficient_funds
payment_credential_expired
mandate_inactive
otp_or_authentication_issue
unknown
```

## 8. Recovery Case

```json
{
  "case_id": "case_001",
  "event_id": "evt_001",
  "merchant_id": "m_001",
  "customer_id": "c_001",
  "amount": 249900,
  "recoverability": "high",
  "recovery_probability": 0.91,
  "priority_score": 227409,
  "diagnosis": {
    "bucket": "temporary_failure",
    "confidence": 0.96,
    "method": "deterministic"
  },
  "policy": {
    "decision": "AUTO",
    "policy_version": "v1",
    "reasons": [
      "confidence >= 0.85",
      "amount < ₹10,000",
      "attempt_count < 3"
    ]
  },
  "status": "ready",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

Priority score can be:

```text
priority_score = amount_in_rupees * recovery_probability
```

This is intentionally deterministic arithmetic.

## 9. Recovery Action

```json
{
  "action_id": "act_001",
  "case_id": "case_001",
  "action_type": "CREATE_PAYMENT_LINK",
  "autonomy_level": "AUTO",
  "idempotency_key": "revguard-case_001-action_1",
  "status": "created",
  "provider": "razorpay",
  "provider_reference": "plink_xxx",
  "customer_message": {
    "language": "hinglish",
    "message": "Hi Rahul, aapka ₹2,499 subscription payment complete nahi ho paaya...",
    "tone": "polite",
    "prompt_version": "recovery_message_v1",
    "generated_at": "timestamp",
    "sent": true,
    "sent_at": "timestamp"
  },
  "created_at": "timestamp",
  "completed_at": "timestamp"
}
```

**Note**: `customer_message` is populated when a SEND_MESSAGE or CREATE_PAYMENT_LINK action also sends a customer-facing message. Store the actual text at generation time so the UI can display it without re-calling Gemini.

Recommended action types:

```text
CREATE_PAYMENT_LINK
SEND_MESSAGE
SCHEDULE_FOLLOWUP
QUEUE_FOR_REVIEW
BLOCK
```

## 9b. Customer Reply Log (new — needed for opt-out and intent tracking)

```json
{
  "reply_id": "reply_001",
  "case_id": "case_001",
  "customer_id": "c_001",
  "raw_message": "kal kar dena",
  "intent": "ASK_TO_DELAY",
  "promised_date": "2026-09-02",
  "confidence": 0.94,
  "prompt_version": "reply_intent_v1",
  "received_at": "timestamp",
  "processed_at": "timestamp"
}
```

This was missing from the original data model. The reply log is append-only and used for:
- rendering reply history in the case detail audit trail
- enforcing opt-out when intent is STOP
- evidence if a customer disputes the interaction

## 10. Audit Log

Append-only.

```json
{
  "audit_id": "audit_001",
  "case_id": "case_001",
  "event_id": "evt_001",
  "timestamp": "timestamp",
  "actor": "system",
  "stage": "policy",
  "action": "DECISION_MADE",
  "decision": "AUTO",
  "details": {
    "confidence": 0.96,
    "amount": 249900,
    "attempt_count": 1
  }
}
```

## 11. Evaluation Run

```json
{
  "run_id": "run_001",
  "dataset_version": "v1",
  "records": 250,
  "recoverable_cases": 160,
  "recovered_cases": 112,
  "recovered_revenue": 29140000,
  "recovery_rate": 0.70,
  "automation_rate": 0.68,
  "blocked_count": 31,
  "review_count": 57,
  "diagnosis_accuracy": 0.94,
  "created_at": "timestamp"
}
```

Do not copy these example metric values into the pitch. Replace them with measured values from the actual run.

## 12. State machines

### Recovery case

```text
NEW
 ↓
DIAGNOSED
 ↓
POLICY_EVALUATED
 ├── AUTO → ACTION_PENDING → ACTION_SENT → RECOVERY_PENDING → RECOVERED / FAILED
 ├── REVIEW → QUEUED_FOR_REVIEW → APPROVED / REJECTED
 └── BLOCKED → CLOSED
```

### Action

```text
PENDING
 ↓
EXECUTING
 ├── SUCCESS
 ├── FAILED
 └── UNKNOWN
        ↓
   VERIFY STATE
```

## 13. Manual owner actions for this phase

- Seed the database with test documents.
- Verify that amounts are displayed in rupees while stored in paise.
- Create at least one case for each terminal policy outcome:
  - AUTO
  - QUEUE_FOR_REVIEW
  - BLOCKED
- Create at least one ambiguous event that actually calls Gemini.
- Create at least one timeout/unknown-action test case.

## 14. Missing data model elements (found during user flow review)

### 14a. Case lookup by provider_reference

The Razorpay webhook for `payment_link.paid` will not contain `case_id`. The system must be able to look up a recovery case by `provider_reference` (e.g., `plink_xxx`).

Add an index or query capability:
```text
recovery_actions
  WHERE provider_reference = "plink_xxx"
  LIMIT 1
  → returns case_id
```

Firestore does not automatically index sub-fields. Ensure `provider_reference` is a top-level field on `recovery_actions` and that a composite index exists if needed.

### 14b. Opt-out update mechanism

The Customer model has `whatsapp_opt_in: true/false` but no spec describes how it gets updated.

Two paths must exist:

```text
Path 1 — Customer replies STOP:
  Gemini extracts intent: STOP
  Backend sets customer.whatsapp_opt_in = false
  Subsequent cases for this customer: policy → BLOCKED
  Audit: actor=system, action=CUSTOMER_OPT_OUT_SET

Path 2 — Merchant manually updates:
  No UI currently specified. This is acceptable for MVP.
  Seed data should include at least one opted-out customer.
```

### 14c. Missing audit action types

The audit log section documents the schema and a few examples, but the allowed `action` values were never enumerated. Add these to prevent inconsistency across the codebase:

```text
Ingestion:
  EVENT_RECEIVED
  DUPLICATE_EVENT_BLOCKED

Diagnosis:
  DIAGNOSIS_COMPLETED
  AI_DIAGNOSIS_REQUESTED
  AI_DIAGNOSIS_FAILED
  AI_DIAGNOSIS_FALLBACK

Policy:
  DECISION_MADE  (decision: AUTO | QUEUE_FOR_REVIEW | BLOCKED)

Recovery:
  ACTION_CREATED
  ACTION_EXECUTED
  ACTION_FAILED
  ACTION_UNKNOWN
  ACTION_VERIFIED

Customer:
  MESSAGE_GENERATED
  MESSAGE_SENT
  MESSAGE_DELIVERY_FAILED
  CUSTOMER_OPT_OUT_SET
  REPLY_RECEIVED
  REPLY_PARSED

Outcome:
  PAYMENT_LINK_PAID
  CASE_RECOVERED
  CASE_FAILED
  CASE_CLOSED

Human:
  HUMAN_APPROVED
  HUMAN_REJECTED
```

Allowed `actor` values:
```text
system
human
webhook
```

### 14d. Missing CONFUSED intent handling in customer reply

`04_userflows.md` lists `CONFUSED` as an intent but `07_prd_requirements.md` and `03_datamodels.md` omit it from the action model.

When Gemini returns `intent: CONFUSED`:
```text
→ Do NOT auto-execute any action
→ Flag case for QUEUE_FOR_REVIEW if not already
→ Audit: REPLY_PARSED, intent=CONFUSED
→ Optionally: send a simpler follow-up message (only if retry < limit)
```

