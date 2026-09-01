# RevGuard — Product Requirements Document (PRD)

## 1. Product

**RevGuard**

AI-powered bounded revenue recovery for failed recurring payments and UPI mandate auto-debits.

## 2. MVP objective

Given a batch or stream of failed recurring-payment events, RevGuard must:

1. detect the failed event
2. diagnose the likely root cause
3. estimate recoverability
4. select a policy outcome
5. execute or queue a recovery action
6. communicate with the customer when appropriate
7. verify the outcome
8. record the audit trail
9. update recovery metrics

## 3. Target user

Merchant operations / finance user responsible for recurring revenue.

## 4. Functional requirements

### FR-01 — Event ingestion
The system shall accept normalized recurring-payment events.

Acceptance:
- schema validated
- duplicate events do not create duplicate recovery cases

### FR-02 — Deterministic diagnosis
The system shall map known failure codes to root-cause buckets without an LLM.

Acceptance:
- deterministic mapping is logged
- no Gemini call for known codes

### FR-03 — Ambiguous diagnosis
The system shall send only genuinely ambiguous failure messages to Gemini.

Acceptance:
- Gemini output validated against a schema
- malformed output causes review/fallback
- prompt and model result are auditable

### FR-04 — Recovery probability
The system shall compute a recovery probability using deterministic/synthetic logic for the MVP.

It may use:
- historical payment behavior
- failure class
- retry count
- amount
- customer history

The formula must be documented.

### FR-05 — Prioritization
The system shall sort cases by:

```text
amount_in_rupees × recovery_probability
```

No LLM required.

### FR-06 — Policy engine
The system shall evaluate:

```text
If payment already succeeded:
    BLOCKED

If mandate is inactive/cancelled:
    BLOCKED

If customer opted out:
    BLOCKED

If confidence < 0.85:
    QUEUE_FOR_REVIEW

If amount >= ₹10,000:
    QUEUE_FOR_REVIEW

If retry_count >= 3:
    QUEUE_FOR_REVIEW

If non-recoverable:
    BLOCKED

Else:
    AUTO
```

Thresholds are MVP defaults and must be configurable in one policy file/module.

### FR-07 — Recovery action
For AUTO cases, the system shall choose a bounded recovery strategy.

MVP strategies:
- recovery Payment Link
- customer message
- simulated retry/recovery

Do not assume a direct generic recurring-charge retry API exists.

### FR-08 — Customer communication
The system shall generate a short message in the customer's preferred language style.

Supported:
- English
- Hindi
- Hinglish

Gemini output must use structured response validation.

### FR-09 — Customer reply parsing
Optional but recommended after core MVP:
- PAY_NOW
- ASK_TO_DELAY
- STOP
- OTHER

Only extract structured intent/date; never allow free-form model output to directly execute financial actions.

### FR-10 — Idempotency
Every externally meaningful recovery action shall have a unique idempotency key.

Acceptance:
- repeated execution attempt does not duplicate action
- unknown external response triggers state verification

### FR-11 — Audit
The system shall record:
- event received
- diagnosis
- confidence
- policy decision
- action
- provider reference
- outcome
- timestamps
- actor

### FR-12 — Dashboard
The system shall show:
- revenue at risk
- recovered revenue
- recovery rate
- root-cause breakdown
- AUTO / REVIEW / BLOCKED counts
- case table

### FR-13 — Review queue
Human operator can inspect and approve/reject review cases.

### FR-14 — Evaluation
System shall evaluate a synthetic dataset and produce:
- records processed
- recoverable cases
- recovered cases
- recovered revenue
- recovery rate
- automation rate
- blocked count
- review count
- diagnosis accuracy for labeled test cases

## 5. Non-functional requirements

### NFR-01 Reliability
A temporary external API failure must not cause duplicate recovery actions.

### NFR-02 Traceability
Every autonomous action must have a visible audit record.

### NFR-03 Security
Secrets must be environment variables and never committed.

### NFR-04 Explainability
The UI must show why an action was permitted or blocked.

### NFR-05 Reproducibility
The evaluation dataset and scripts must be reproducible.

### NFR-06 Simplicity
Single backend deployment; no microservice requirement.

## 6. Explicitly out of scope

- Checkout abandonment
- B2B receivables
- Multi-agent orchestration
- Production-scale benchmarks
- Live-money payments
- Automatic discounting
- Autonomous arbitrary customer communication
- Full CRM
- Full WhatsApp assistant

## 7. MVP priorities

### P0 — absolutely required
- ingestion
- diagnosis
- policy
- recovery action
- idempotency
- audit
- dashboard
- evaluation dataset
- failure scenario

### P1 — strongly recommended
- WhatsApp sandbox/mock provider
- customer reply extraction
- review queue

### P2 — only if P0/P1 are complete
- advanced analytics
- richer personalization
- additional dashboards

## 8. Manual owner actions

At PRD lock:
- sign off on the policy thresholds
- select final recovery action path
- confirm which external integrations will actually be used
- refuse new features until P0 is complete

At end of each coding phase:
- manually run acceptance scenarios listed in `task_plan.md`.

## 9. Additional functional requirements (found during user-flow review)

### FR-15 — Automated outcome verification via webhook
The system shall automatically mark a recovery case as RECOVERED when Razorpay fires a `payment_link.paid` (or equivalent) webhook.

Acceptance:
- Webhook signature verified before processing.
- Recovery case found by `provider_reference`, not assumed by `case_id`.
- Audit record written with `actor=webhook`.
- Duplicate webhook delivery does not create a duplicate RECOVERED state.
- HTTP 200 always returned to Razorpay.

### FR-16 — Customer opt-out enforcement
When a customer replies with STOP intent (extracted by Gemini), the system shall:
- Set `customer.whatsapp_opt_in = false`.
- Immediately block any further automated outreach for all open cases.
- Write an audit record.

Acceptance:
- A case that was AUTO before opt-out is re-evaluated to BLOCKED.
- No further messages are sent.
- Opt-out is permanent until manually reset (out of MVP scope).

### FR-17 — Message preview in UI
The case detail view shall show the exact customer message that was generated and sent.

Acceptance:
- Message text is stored at generation time.
- UI renders it verbatim (not regenerated on page load).
- Prompt version and language are shown alongside.

## 10. Additional non-functional requirements (found during user-flow review)

### NFR-07 Firestore query coverage
All queries required by the API (especially `provider_reference` lookup on `recovery_actions`) must be backed by Firestore indexes. Missing indexes cause runtime failures in production that are invisible in the emulator.

Manual owner check: test the webhook lookup path with a real `payment_link.paid` event in Razorpay Test Mode, not just unit tests.

