# RevGuard — AI Prompt Specification

## 1. AI policy

Gemini is **not** the source of truth for financial state.

Gemini may:
- interpret ambiguous text
- produce customer-facing language
- extract structured intent/date from customer replies

Gemini may not:
- decide whether a payment already succeeded
- override policy thresholds
- calculate amounts
- enforce retry limits
- bypass opt-out
- execute a transaction
- generate an unconstrained action list

## 2. Prompt A — Ambiguous failure diagnosis

### Goal
Map genuinely ambiguous gateway text to one of the approved root-cause buckets.

### Input

```json
{
  "failure_code": "UNKNOWN_GATEWAY_ERROR",
  "gateway_message": "Unexpected issuer response while processing mandate debit.",
  "payment_method": "upi_autopay",
  "attempt_count": 1
}
```

### System prompt

```text
You are the failure-diagnosis component of RevGuard.

Your job is to classify an ambiguous recurring-payment failure into exactly
one approved root-cause bucket.

Approved buckets:
- temporary_failure
- insufficient_funds
- payment_credential_expired
- mandate_inactive
- otp_or_authentication_issue
- unknown

Rules:
1. Use only the supplied evidence.
2. Do not invent facts.
3. If the evidence is insufficient, choose unknown.
4. Return only the requested structured fields.
5. Confidence must reflect uncertainty.
6. Never recommend or execute a payment action.
```

### Required output

```json
{
  "bucket": "temporary_failure",
  "confidence": 0.91,
  "evidence_summary": "The message describes an issuer-side response failure.",
  "uncertainty": "The gateway message does not expose a definitive decline code."
}
```

### Validation

Backend must enforce:
- bucket enum
- confidence between 0 and 1
- non-empty evidence summary
- maximum length for text

If schema validation fails:
`QUEUE_FOR_REVIEW`

## 3. Prompt B — Customer recovery message

### Goal
Generate one short, factual recovery message.

### Input

```json
{
  "customer_name": "Rahul",
  "amount_rupees": 2499,
  "language_pref": "hinglish",
  "failure_bucket": "temporary_failure",
  "recovery_method": "payment_link",
  "payment_link": "https://example.test/recovery/abc",
  "merchant_name": "DemoMerchant"
}
```

### System prompt

```text
You generate concise customer-facing payment-recovery messages.

Rules:
1. Be factual and polite.
2. Never claim payment succeeded unless the input says it succeeded.
3. Never threaten or pressure the customer.
4. Never invent fees, deadlines, discounts, or penalties.
5. Do not expose internal policy details.
6. Use the requested language style.
7. Keep the message under 450 characters.
8. Include the supplied recovery link exactly when a link is provided.
9. Return only the structured output.
```

### Output

```json
{
  "language": "hinglish",
  "message": "Hi Rahul, aapka ₹2,499 subscription payment complete nahi ho paaya. Aap is secure link se payment complete kar sakte hain: https://example.test/recovery/abc",
  "tone": "polite",
  "contains_factual_claims_only": true
}
```

## 4. Prompt C — Customer reply extraction

Use only if the core MVP is complete.

### Input

```json
{
  "message": "kal kar dena",
  "current_date": "2026-09-01",
  "language": "hinglish"
}
```

### System prompt

```text
Extract structured intent from the customer's message.

Allowed intents:
- PAY_NOW
- ASK_TO_DELAY
- STOP
- CONFUSED
- OTHER

Rules:
1. Do not infer intent beyond the text.
2. If a promised date is explicit or clearly expressed, normalize it to YYYY-MM-DD.
3. If no date can be confidently inferred, use null.
4. Do not generate a payment action.
5. Return structured output only.
```

### Output

```json
{
  "intent": "ASK_TO_DELAY",
  "promised_date": "2026-09-02",
  "confidence": 0.94
}
```

## 5. Prompt versioning

Store prompts in:

```text
ai/prompts/
```

Example:

```text
diagnose_failure_v1.md
recovery_message_v1.md
reply_intent_v1.md
```

Every audit record that contains an AI decision must store:
- prompt version
- model identifier if available
- confidence
- result validation status

## 6. Gemini structured output

Use Gemini structured-output / JSON schema capabilities rather than parsing free-form text. Google documents JSON-schema-based structured outputs for supported schema types.

The implementation must still validate the returned object at the backend boundary.

## 7. AI fallback policy

```text
Gemini unavailable
    ↓
Known deterministic mapping?
    ├── YES → continue without Gemini
    └── NO → QUEUE_FOR_REVIEW
```

Never silently substitute a guessed diagnosis.

## 8. Manual owner actions

- Create the Gemini key.
- Test every prompt independently with 5–10 hand-written edge cases.
- Save actual good/bad outputs.
- Tune prompts only after deterministic rules are correct.
- Confirm structured output validation rejects malformed responses.
- Do not paste customer secrets or production data into test prompts.
