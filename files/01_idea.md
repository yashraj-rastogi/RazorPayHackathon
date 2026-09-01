# RevGuard — Idea / Product Thesis

## 1. One-line pitch

**RevGuard is an AI-powered revenue recovery controller for failed recurring payments and UPI mandate auto-debits.** It detects recoverable payment failures, diagnoses their likely cause, chooses a bounded recovery action, communicates with the customer when appropriate, and records the complete audit trail.

## 2. The problem

Recurring revenue can silently leak when a scheduled payment fails because of transient bank/gateway issues, insufficient funds, expired payment credentials, inactive mandates, or ambiguous gateway responses.

A merchant should not have to manually inspect every failed renewal and decide:

- Is this failure recoverable?
- What caused it?
- Should we retry, contact the customer, or stop?
- Is it safe to automate?
- Has this transaction already succeeded?
- Have we already contacted/retried too many times?

The product turns those questions into a controlled recovery workflow.

## 3. What we are building in the 4-day MVP

We deliberately solve **one revenue leak type deeply**:

> Failed recurring payments / UPI mandate auto-debits.

We are **not** building separate checkout-abandonment, receivables, or multi-leak modules in the MVP.

The architecture uses a generic revenue-event shape so those sources can be added later without rewriting the core pipeline.

## 4. Core loop

```text
Recurring payment failure
        ↓
Ingest event
        ↓
Diagnose root cause
        ↓
Calculate recovery opportunity
        ↓
Policy decision
   ┌────┼───────────┐
   ↓    ↓           ↓
 AUTO  REVIEW    BLOCKED
   ↓
Generate recovery action
   ↓
Execute / communicate
   ↓
Verify outcome
   ↓
Audit + metrics
```

## 5. Product differentiator

The differentiator is **bounded autonomy**.

RevGuard does not give an LLM unrestricted authority over payment actions.

### AI is used for:
1. Ambiguous failure-message interpretation.
2. Customer-facing recovery-message generation.
3. Optional structured extraction of customer replies.

### Deterministic code is used for:
1. Payment/subscription state checks.
2. Retry limits.
3. Monetary thresholds.
4. Customer opt-out enforcement.
5. Idempotency and duplicate prevention.
6. Policy gates.
7. Action execution.
8. Audit logging.
9. Metrics.

### Core thesis

> **AI handles ambiguity; deterministic software handles financial correctness.**

## 6. Important implementation reality

Razorpay Subscriptions support recurring payments, including UPI Autopay, and expose subscription APIs and webhook events. For a recovery flow, the MVP should not assume there is a generic "retry failed recurring charge" endpoint. Instead, recovery can be demonstrated using a safe customer-initiated recovery path such as generating a Razorpay Payment Link, while the simulator models the recurring-payment failure/recovery lifecycle. Verify exact API behavior in Razorpay Test Mode before recording the final demo.

Razorpay documents Subscription APIs and webhook events, and Payment Links can be created through `POST /v1/payment_links`. [See API/spec file for references.]

## 7. Target user

Primary user: **merchant / merchant operations or finance user**.

The merchant wants to answer:

> "How much recurring revenue is currently at risk, which cases are worth acting on, what did RevGuard do, and how much money did we recover?"

## 8. Success criteria

The MVP is successful if a judge can see, end-to-end:

1. A recurring payment failure arrives.
2. RevGuard diagnoses it.
3. The policy engine decides whether automation is permitted.
4. A customer recovery action is generated.
5. The action is executed or simulated safely.
6. The resulting recovery is recorded.
7. The dashboard metrics update.
8. A blocked/review case proves the system can deliberately refuse to act.
9. A timeout/ambiguous-result failure demonstrates idempotent recovery.

## 9. Non-goals

Do not add these unless every core requirement is already finished:

- Multiple revenue-leak modules.
- Multi-agent orchestration.
- Vector database / RAG.
- Complex autonomous planning.
- Production-scale 10k+ benchmark claims.
- Long conversational WhatsApp bot.
- Real-money payment execution.
- Unbounded payment retries.
- Claims of production readiness.

## 10. Positioning

Suggested pitch:

> **"RevGuard closes the loop on recurring payment failures: it detects revenue at risk, diagnoses why the payment failed, chooses a bounded recovery action, and knows when not to act."**

Alternative tagline:

> **Detect. Diagnose. Decide. Recover.**

## 11. Manual owner actions

At the start of the project, the human owner must:

- Create/verify Razorpay Test Mode access.
- Create the Gemini API key.
- Decide whether WhatsApp will be a live Twilio sandbox or a demo-only simulated sender.
- Keep all secrets out of GitHub.
- Confirm the exact APIs available in the test environment before implementation.
- Maintain a short engineering log of real failures for the final "What broke, and how we got out" section.

Do not proceed to UI polish until the core end-to-end loop works.
