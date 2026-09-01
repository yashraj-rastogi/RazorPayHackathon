# RevGuard — 4-Day Task Plan / Roadmap

## Deadline

**Submission: 5 September 2026**

This roadmap assumes a solo builder with approximately four effective build days.

The rule:

> **Do not add new scope until the current phase passes its acceptance test.**

---

# PHASE 0 — LOCK THE PRODUCT

## Goal

Freeze the project before coding.

### Tasks

- [ ] Confirm name: RevGuard or replacement
- [ ] Confirm scope: failed recurring payments / UPI mandate auto-debits
- [ ] Confirm backend stack
- [ ] Create repository
- [ ] Create project board/checklist
- [ ] Create `.env.example`
- [ ] Create Firestore project
- [ ] Create Razorpay Test Mode access
- [ ] Create Gemini API key
- [ ] Decide Twilio sandbox vs mock provider
- [ ] Copy these markdown specs into the repo

### Manual owner actions

YOU MUST:
1. Create all external accounts/credentials.
2. Verify API access manually.
3. Put only placeholder names in `.env.example`.
4. Add secrets to local environment / deployment secrets.
5. Make the GitHub repository public only when you are ready; never expose credentials.
6. Start `docs/engineering-log.md`.

### Acceptance test

You can answer:

> What are we building, what are we not building, and which external services are actually available?

---

# PHASE 1 — SYNTHETIC DATA ENGINE

## Goal

Generate a deterministic, varied recurring-payment dataset.

### Tasks

- [ ] Define seedable generator
- [ ] Generate 200–300 records
- [ ] Include known failure types
- [ ] Include ambiguous gateway messages
- [ ] Include retry-limit cases
- [ ] Include already-successful cases
- [ ] Include opt-out cases
- [ ] Include varied amounts
- [ ] Include language preferences
- [ ] Create labels for evaluation
- [ ] Save `dataset_version`

### Suggested files

```text
data/
  generator.py
  seed/
  generated/
evaluation/
  labels.json
```

### Manual owner actions

Run the generator yourself.

Spot-check at least 20 records.

Confirm:
- records are not all identical
- edge cases exist
- labels make sense
- amounts are realistic
- no fake "recovered" metric is injected

### Acceptance test

One command regenerates the same dataset when given the same seed.

---

# PHASE 2 — CORE BACKEND PIPELINE

## Goal

Make the core loop work without UI.

### Tasks

- [ ] Event ingestion
- [ ] Duplicate event detection
- [ ] Firestore persistence
- [ ] Deterministic diagnosis
- [ ] Recovery probability logic
- [ ] Policy engine
- [ ] Recovery action abstraction
- [ ] Audit logging
- [ ] Case state machine

### Golden CLI / API test

```text
event
 → diagnosis
 → recovery probability
 → policy
 → action
 → audit
```

### Manual owner actions

You personally test:

### AUTO
A low-value retryable failure.

### REVIEW
A high-value or low-confidence case.

### BLOCKED
An opt-out case.

### BLOCKED
Already successful payment.

### REVIEW
Retry count >= 3.

### Acceptance test

All three policy decisions are reproducible and appear in Firestore with audit trails.

---

# PHASE 3 — GEMINI

## Goal

Add AI only where it earns its place.

### Tasks

- [ ] Ambiguous diagnosis prompt
- [ ] Structured output schema
- [ ] Backend validation
- [ ] Fallback to REVIEW
- [ ] Recovery message prompt
- [ ] Language variation
- [ ] Store prompt version
- [ ] Store model result metadata

### Manual owner actions

Create a manual test sheet with at least:

1. Known failure code.
2. Ambiguous transient failure.
3. Clearly insufficient funds.
4. Clearly inactive mandate.
5. Nonsense gateway message.
6. Missing gateway message.

Confirm:
- deterministic cases do not call Gemini
- ambiguous case does
- malformed AI output cannot trigger recovery

### Acceptance test

A judge can understand why AI is used without you saying "AI is everywhere."

---

# PHASE 4 — RECOVERY ACTION

## Goal

Complete one real/simulated money-recovery path safely.

### Preferred MVP

For eligible AUTO cases:
- create a Razorpay Payment Link or invoke the verified test-mode recovery mechanism
- generate customer message
- record provider reference
- verify eventual outcome

### Tasks

- [ ] Razorpay provider abstraction
- [ ] Test-mode integration
- [ ] Payment Link path if selected
- [ ] Messaging provider abstraction
- [ ] Gemini recovery message
- [ ] Store generated message text verbatim in Firestore (required for FR-17 preview)
- [ ] Audit provider response
- [ ] Outcome verification
- [ ] Webhook handler: POST /api/v1/webhooks/razorpay
- [ ] Webhook: look up recovery case by provider_reference (not case_id)
- [ ] Webhook: mark action SUCCESS + case RECOVERED on payment_link.paid
- [ ] Webhook: idempotent (duplicate webhook does not double-mark RECOVERED)
- [ ] Webhook: always return HTTP 200 to Razorpay
- [ ] Customer opt-out: when Gemini returns intent STOP, set whatsapp_opt_in=false
- [ ] Customer opt-out: re-evaluate open AUTO cases for opted-out customer → BLOCKED

### Manual owner actions

Run the recovery path manually.

Verify:
- provider reference appears
- message contains correct amount
- no false payment-success claim
- recovery case changes state
- audit trail is complete

### Acceptance test

One case goes from:

```text
FAILED
→ AUTO
→ ACTION
→ RECOVERED
```

without manual database edits.

---

# PHASE 5 — IDEMPOTENCY + FAILURE RECOVERY

## Goal

Create the strongest engineering story in the project.

### Tasks

- [ ] Implement action_id
- [ ] Implement Idempotency-Key handling
- [ ] Implement state re-check
- [ ] Simulate provider timeout
- [ ] Mark action UNKNOWN
- [ ] Verify state
- [ ] Safely decide whether follow-up action is permitted
- [ ] Log failure and fix

### Manual owner actions — THIS IS CRITICAL

Actually trigger the failure.

Record:

```text
What we expected
What actually happened
Root cause
Risk created
Fix
Test after fix
```

Take screenshots/log snippets while you still have them.

Do not invent this story later.

### Acceptance test

Repeat the same recovery request twice.

The second attempt must not create a duplicate action.

---

# PHASE 6 — DASHBOARD

## Goal

Turn the engine into a judge-readable product.

### Build in order

1. Summary metrics (from live Firestore cases, NOT from evaluation_run)
2. Case table (sorted by priority_score desc)
3. Case detail
4. Why acted / Why not acted sections
5. Message preview (render stored message text, do NOT regenerate)
6. Review queue (with badge count on nav item when count > 0)
7. Audit trail timeline
8. Metrics screen (from evaluation_run, separate from dashboard)

### Manual owner actions

Open the dashboard and ask:

> Can a judge understand the system without me explaining every field?

If not, simplify.

Verify:
- Dashboard metrics come from live case queries, not hard-coded.
- Message preview shows what was actually sent.
- Review queue badge appears when cases are pending.
- Audit trail timestamps are real.

### Acceptance test

A single AUTO case can be followed from dashboard to audit trail in under 5 clicks.

---

# PHASE 7 — EVALUATION

## Goal

Generate honest metrics from the actual system.

### Tasks

- [ ] Run seeded dataset
- [ ] Produce labeled evaluation output
- [ ] Calculate diagnosis accuracy
- [ ] Calculate recovery rate
- [ ] Calculate automation rate
- [ ] Calculate blocked/review counts
- [ ] Calculate recovered revenue
- [ ] Save evaluation artifact

### Manual owner actions

Run the full evaluation yourself.

Check a random sample against the ground truth.

Do not adjust the dataset after seeing the results just to make the numbers look better.

If results are weak:
- explain why
- improve the system
- rerun
- keep the final metric reproducible

### Acceptance test

The exact evaluation command reproduces the final metrics.

---

# PHASE 8 — GITHUB / DOCUMENTATION

## Goal

Make the repo inspectable by an engineer.

### README must contain

- problem
- product
- architecture
- AI judgment
- policy engine
- setup
- environment variables
- dataset generation
- evaluation
- screenshots
- results
- failure recovery
- limitations
- future scope

### Manual owner actions

Clone the repo into a clean directory.

Follow your own README from scratch.

Fix every missing step.

Then:
- remove API keys
- check `.gitignore`
- inspect Git history for accidental secrets
- verify deployed URLs
- add license only if appropriate
- make the repo look finished

---

# PHASE 9 — 5-MINUTE VIDEO

## Golden path

### 0:00–0:25
Problem + revenue at risk.

### 0:25–0:50
RevGuard concept.

### 0:50–2:40
AUTO recovery case:
- failure
- diagnosis
- policy
- message/payment link
- recovery

### 2:40–3:15
BLOCKED or REVIEW case:
- show restraint

### 3:15–4:05
What broke:
- timeout
- ambiguous state
- idempotency/state verification fix

### 4:05–4:40
AI judgment:
- where Gemini is used
- where it is deliberately NOT used

### 4:40–5:00
Actual evaluation metrics + final statement.

### Manual owner actions

YOU must:
- write the script
- rehearse with a timer
- record 3+ takes
- choose the strongest take
- verify every claim in the narration against the repo
- add captions/text overlays only where they help
- watch the final video once without pausing

Never exceed five minutes.

---

# PHASE 10 — FINAL SUBMISSION AUDIT

## Product

- [ ] Core flow works
- [ ] AUTO works
- [ ] REVIEW works
- [ ] BLOCKED works
- [ ] Idempotency works
- [ ] Failure recovery works
- [ ] Dashboard numbers are real
- [ ] Evaluation reproduces metrics

## AI

- [ ] Structured output
- [ ] Known cases avoid unnecessary LLM calls
- [ ] AI failure falls back safely
- [ ] Prompts are versioned
- [ ] No hidden secrets

## Razorpay

- [ ] Test Mode only
- [ ] External API calls verified
- [ ] Webhook handling verified if used
- [ ] Provider references visible
- [ ] No unsupported API claims

## GitHub

- [ ] README complete
- [ ] Setup works
- [ ] `.env.example`
- [ ] `.gitignore`
- [ ] No credentials
- [ ] Architecture diagram
- [ ] Evaluation script
- [ ] Failure document

## Video

- [ ] Under 5 minutes
- [ ] Problem obvious
- [ ] Demo works
- [ ] AI judgment explicit
- [ ] Failure story real
- [ ] Metrics real
- [ ] No unnecessary team introduction

## Manual owner action — final 2 hours

**Freeze the code.**

Do not add features.

Only:
- fix blocking bugs
- update README
- rerun tests
- verify links
- upload video
- submit
