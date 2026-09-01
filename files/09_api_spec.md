# RevGuard — API Specification

## 1. API principles

- RESTful JSON API.
- Backend owns business rules.
- Frontend never calls Razorpay/Gemini directly.
- Secrets remain server-side.
- Every mutating recovery endpoint must be idempotent where relevant.
- External-provider details are abstracted behind services.

## 2. Internal endpoint summary

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/dashboard/summary` | Financial and policy summary |
| GET | `/api/v1/cases` | List recovery cases |
| GET | `/api/v1/cases/{case_id}` | Case detail |
| POST | `/api/v1/events` | Ingest one event |
| POST | `/api/v1/events/seed` | Seed synthetic dataset |
| POST | `/api/v1/cases/{case_id}/diagnose` | Run diagnosis |
| POST | `/api/v1/cases/{case_id}/evaluate-policy` | Run policy |
| POST | `/api/v1/cases/{case_id}/recover` | Execute approved recovery |
| POST | `/api/v1/cases/{case_id}/approve` | Approve review case |
| POST | `/api/v1/cases/{case_id}/reject` | Reject review case |
| GET | `/api/v1/cases/{case_id}/audit` | Audit trail |
| GET | `/api/v1/cases/{case_id}/message` | Preview the generated customer message |
| GET | `/api/v1/metrics` | Evaluation/product metrics |
| POST | `/api/v1/simulate/failure` | Demo/testing failure injection |
| POST | `/api/v1/webhooks/razorpay` | Razorpay webhook receiver (payment_link.paid etc.) |
| POST | `/api/v1/customers/{customer_id}/opt-out` | Record customer opt-out |

## 3. Dashboard summary

### Request

```http
GET /api/v1/dashboard/summary
```

### Response

```json
{
  "revenue_at_risk": 1842000,
  "revenue_recovered": 738000,
  "recovery_rate": 0.628,
  "cases": {
    "auto": 116,
    "review": 42,
    "blocked": 39
  },
  "root_causes": {
    "temporary_failure": 84,
    "insufficient_funds": 61,
    "payment_credential_expired": 23,
    "mandate_inactive": 17,
    "unknown": 12
  }
}
```

Values are examples only.

## 4. Event ingestion

### Request

```http
POST /api/v1/events
Content-Type: application/json
```

```json
{
  "event_id": "evt_001",
  "revenue_type": "recurring_payment",
  "merchant_id": "m_001",
  "customer_id": "c_001",
  "subscription_id": "sub_001",
  "amount": 249900,
  "currency": "INR",
  "status": "failed",
  "reason": "BANK_TIMEOUT",
  "gateway_message": "Unexpected issuer response",
  "attempt_count": 1
}
```

### Behavior

1. Validate schema.
2. Check duplicate event.
3. Store event.
4. Create recovery case.
5. Trigger diagnosis.

## 5. Case listing

```http
GET /api/v1/cases?decision=AUTO&status=READY&limit=50
```

Supported filters:
- decision
- status
- root cause
- minimum amount
- maximum amount

## 6. Case detail

```http
GET /api/v1/cases/{case_id}
```

Response must include:
- event
- diagnosis
- recovery probability
- policy
- available action
- current status

## 7. Policy evaluation

```http
POST /api/v1/cases/{case_id}/evaluate-policy
```

Response:

```json
{
  "decision": "AUTO",
  "policy_version": "v1",
  "reasons": [
    "diagnosis_confidence >= 0.85",
    "amount < 10000 INR",
    "retry_count < 3",
    "customer opt-in present"
  ]
}
```

## 8. Recover

```http
POST /api/v1/cases/{case_id}/recover
Idempotency-Key: revguard-case_001-recover_1
```

Request:

```json
{
  "action_type": "CREATE_PAYMENT_LINK"
}
```

Backend sequence:

```text
1. Load case.
2. Re-check current payment/subscription state.
3. Re-check policy.
4. Check idempotency.
5. Create safe recovery action.
6. Persist provider reference.
7. Write audit event.
8. Return result.
```

Response:

```json
{
  "action_id": "act_001",
  "status": "CREATED",
  "provider": "razorpay",
  "provider_reference": "plink_xxx",
  "recovery_url": "https://rzp.io/i/example"
}
```

## 9. Review approval

```http
POST /api/v1/cases/{case_id}/approve
```

Backend must re-check:
- current state
- policy
- idempotency

Do not trust an old browser decision.

## 10. Review rejection

```http
POST /api/v1/cases/{case_id}/reject
```

Request:

```json
{
  "reason": "Merchant chose not to contact customer again."
}
```

## 11. Audit

```http
GET /api/v1/cases/{case_id}/audit
```

Response:

```json
{
  "case_id": "case_001",
  "events": [
    {
      "timestamp": "2026-09-01T10:04:12Z",
      "stage": "ingestion",
      "action": "EVENT_RECEIVED"
    },
    {
      "timestamp": "2026-09-01T10:04:12Z",
      "stage": "diagnosis",
      "action": "DIAGNOSIS_COMPLETED"
    }
  ]
}
```

## 12. Seed endpoint

Development only:

```http
POST /api/v1/events/seed
```

Request:

```json
{
  "count": 250,
  "dataset_version": "v1",
  "seed": 42
}
```

The API should return:
- records created
- dataset version
- reproducibility seed

Disable or protect this endpoint outside demo/dev environments.

## 13. Failure simulation

Development/demo only:

```http
POST /api/v1/simulate/failure
```

Example:

```json
{
  "type": "razorpay_timeout",
  "case_id": "case_001"
}
```

Allowed:
- razorpay_timeout
- gemini_timeout
- malformed_ai_output
- duplicate_event
- already_successful
- retry_limit

This endpoint exists only to reproduce failure handling during testing/demo.

## 14. External Razorpay integration notes

Current Razorpay documentation exposes Subscription APIs for recurring payments and Subscription webhook events. Razorpay also documents creating Standard Payment Links through:

```text
POST /v1/payment_links
```

The recovery implementation should use only endpoints verified in Test Mode.

Do not invent an unsupported `retry subscription payment` endpoint.

Recommended abstraction:

```python
class PaymentProvider:
    def get_payment_state(...)
    def create_recovery_payment_link(...)
    def verify_payment_link(...)
```

A concrete Razorpay implementation can back this interface.

## 15. External webhook endpoint

```http
POST /api/v1/webhooks/razorpay
```

Responsibilities:
- verify webhook authenticity according to Razorpay's current webhook documentation
- normalize supported events
- enforce idempotent event processing
- never trigger duplicate recovery actions

Do not hard-code an event list without checking current Razorpay webhook documentation before final implementation.

## 16. API error model

```json
{
  "error": {
    "code": "POLICY_BLOCKED",
    "message": "Automatic recovery is not permitted for this case.",
    "details": {
      "reason": "RETRY_LIMIT_EXCEEDED"
    }
  }
}
```

Suggested codes:

```text
VALIDATION_ERROR
NOT_FOUND
DUPLICATE_EVENT
POLICY_BLOCKED
REVIEW_REQUIRED
IDEMPOTENCY_CONFLICT
PROVIDER_TIMEOUT
PROVIDER_ERROR
AI_VALIDATION_FAILED
```

## 17. Manual owner actions

Before implementing external calls:
- verify current Razorpay Test Mode API docs
- create test credentials
- test each endpoint manually with curl/Postman
- confirm response payloads
- verify webhook signature handling
- note any API limitation in the README

During development:
- test every mutating endpoint twice
- ensure second call is safe/idempotent
- inspect Firestore audit records

Before video:
- choose whether the actual recovery action will be a Razorpay Payment Link or a simulation
- run the exact API path from a clean state

## 18. Message preview endpoint (added during user-flow review)

```http
GET /api/v1/cases/{case_id}/message
```

Response:

```json
{
  "case_id": "case_001",
  "language": "hinglish",
  "message": "Hi Rahul, aapka ₹2,499 subscription payment complete nahi ho paaya...",
  "tone": "polite",
  "contains_factual_claims_only": true,
  "generated_at": "2026-09-01T10:04:14Z",
  "prompt_version": "recovery_message_v1",
  "sent": true,
  "sent_at": "2026-09-01T10:04:15Z"
}
```

This allows Screen 3 (Case Detail) to render the message preview exactly as it was sent. The UI shows this in the Messaging Preview component (see `06_ui_ux_guidelines.md` section 11).

## 19. Webhook case-lookup behavior (added during user-flow review)

When `POST /api/v1/webhooks/razorpay` receives a `payment_link.paid` event:

```text
1. Verify webhook signature (HMAC, per Razorpay docs).
2. Extract provider_reference from webhook payload (payment link ID).
3. Query recovery_actions WHERE provider_reference = <id>.
4. If found: mark action SUCCESS, mark case RECOVERED.
5. Write audit: actor=webhook, action=PAYMENT_LINK_PAID.
6. Update dashboard metrics (recalculate on next GET /summary).
7. If not found: log warning, do not error — may be an unrelated payment link.
8. Return HTTP 200 immediately (Razorpay retries on non-2xx).
```

**Critical**: Always return 200 to Razorpay even if the payment link is not in your system. Non-2xx causes Razorpay to retry, which can cause duplicate processing.

## 20. Customer opt-out endpoint (added during user-flow review)

```http
POST /api/v1/customers/{customer_id}/opt-out
```

Request:

```json
{
  "reason": "CUSTOMER_REQUESTED",
  "source": "reply_intent"
}
```

Behavior:
1. Set `customer.whatsapp_opt_in = false`.
2. Write audit: `actor=system, action=CUSTOMER_OPT_OUT_SET`.
3. Any open AUTO cases for this customer are re-evaluated: result = BLOCKED.
4. Return confirmation.

This is called internally by the reply-intent handler when Gemini returns `intent: STOP`. It is NOT a public customer-facing endpoint.
