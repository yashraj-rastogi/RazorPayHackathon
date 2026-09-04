# RevGuard — Engineering Log: What Broke & How We Recovered

> This document records real engineering failures encountered during the 4-day build and the deterministic fixes applied. Every entry is a genuine incident, not a manufactured narrative.

---

## 1. Gemini API Rate-Limit Exhaustion (429 Quota Exceeded)

**What happened:** During batch evaluation of 250 synthetic records, the Gemini API (`gemini-flash-latest`) returned `429 Quota Exceeded` after ~20 requests. The free-tier daily limit was silently reached, causing diagnosis calls to fail mid-pipeline.

**Impact:** Any case requiring AI diagnosis would hang or crash the ingestion pipeline.

**How we recovered:** The diagnosis service already had a deterministic fallback path. When Gemini returns an error (timeout, 429, malformed output), the system:
1. Logs the failure with the exact error message.
2. Falls back to `bucket: "unknown"`, `confidence: 0.5`, `method: "fallback"`.
3. The low confidence automatically triggers `QUEUE_FOR_REVIEW` in the policy engine — ensuring no unsafe autonomous action occurs.

**Lesson:** AI fallback is not optional in financial systems. The bounded autonomy thesis proved its value in a real failure scenario — the system degraded gracefully instead of crashing or making unsafe decisions.

---

## 2. Firebase Composite Index Missing (FailedPrecondition 400)

**What happened:** Firestore queries combining a `where()` filter (e.g., `policy.decision == "QUEUE_FOR_REVIEW"`) with `order_by("priority_score")` require a pre-built composite index. Without it, Firestore throws `google.api_core.exceptions.FailedPrecondition: 400 The query requires an index`.

**Impact:** The Cases Ledger page returned HTTP 500 errors. The Review Queue was completely broken. Audit trail queries for individual cases also failed.

**How we recovered:** Added resilient try/except fallback in all three query endpoints (`list_cases`, `get_audit`, `get_message`). When the composite index query fails, the system:
1. Re-issues the query without `order_by`.
2. Sorts the results in-memory in Python.
3. Returns identical results to the frontend — completely transparent to the user.

The Firestore Console also provides 1-click index creation URLs in the error message, so the permanent fix is a single click.

**Lesson:** Firestore's index requirement is invisible during local development with small datasets. Always test filtered + ordered queries against the live database before demo day.

---

## 3. GitHub Push Protection Blocked Credentials

**What happened:** `git push` was rejected by GitHub's Push Protection scanner. The Firebase Admin SDK service account JSON file (`rev-gaurd-firebase-adminsdk-fbsvc-*.json`) was committed to the repository, and GitHub detected it as a `Google Cloud Service Account Credentials` secret.

**Impact:** Could not push any code to the remote repository until the secret was removed from Git history.

**How we recovered:**
1. Added `*-firebase-adminsdk-*.json` and `serviceaccount*.json` to `.gitignore`.
2. Ran `git rm --cached` to untrack the file.
3. Reset the unpushed commit containing the credentials.
4. Pushed a clean commit that passed GitHub's scanner.

**Lesson:** Always add credential file patterns to `.gitignore` *before* the first commit, not after.

---

## 4. Pydantic V2 Field Assignment Error

**What happened:** The `RecoveryCase` model (Pydantic V2 `BaseModel`) did not declare `attempt_count` as an explicit field. When the scoring service tried to set `case.attempt_count = value`, Pydantic V2's strict validation rejected the assignment silently, causing the scoring pipeline to crash.

**Impact:** No cases could be scored or evaluated. The entire ingestion pipeline was blocked.

**How we recovered:** Added `attempt_count: Optional[int] = 1` as an explicit field on the `RecoveryCase` model. Pydantic V2 requires all assignable attributes to be declared in the model schema — unlike V1 which allowed arbitrary attribute assignment.

**Lesson:** Pydantic V2's strictness is a feature, not a bug. Declare every field explicitly.

---

## 5. Customer Phone Number Empty — WhatsApp Messages Not Sending

**What happened:** After enabling the Twilio WhatsApp provider, recovery actions completed successfully (Razorpay links were created) but no WhatsApp messages were delivered. The `customer.phone` field was an empty string `""` because the synthetic dataset generates customer IDs (`c_001`, `c_012`) that don't have corresponding records in the `customers` Firestore collection.

**Impact:** The message dispatch code checked `if customer.whatsapp_opt_in and customer.phone:` — the empty phone caused the entire messaging block to be skipped silently.

**How we recovered:** Updated the recovery service to fall back to `TWILIO_TEST_PHONE_OVERRIDE` from the environment when no customer phone is stored. This ensures demo/test messages always reach the developer's personal WhatsApp number.

**Lesson:** Always test the complete end-to-end path with real external services, not just unit tests with mocked dependencies.

---

## 6. React Hooks Order Violation

**What happened:** New `useState` hooks for the Judge Pitch Demo modal were placed *after* an early `if (loading) return ...` statement in `Dashboard.jsx`. On the first render (while loading), these hooks were never called. On the second render (after data loaded), React detected a different number of hooks and crashed with: "Rendered more hooks than during the previous render."

**Impact:** The entire Dashboard page crashed with a white screen and console errors.

**How we recovered:** Moved all `useState` declarations to the top of the component function, before any conditional returns. React's Rules of Hooks require that hooks are called in the same order on every render.

**Lesson:** React hooks must never appear after conditional returns. This is a fundamental rule that's easy to violate when adding features iteratively.

---

## Summary

| # | Failure | Root Cause | Recovery Strategy | Time to Fix |
|---|---|---|---|---|
| 1 | Gemini 429 rate limit | Free-tier quota exhaustion | Deterministic fallback → REVIEW | Already built in |
| 2 | Firestore composite index | Missing index for filter + order_by | In-memory sorting fallback | 15 minutes |
| 3 | GitHub Push Protection | Credentials in Git history | `.gitignore` + history rewrite | 10 minutes |
| 4 | Pydantic V2 field error | Undeclared model attribute | Explicit field declaration | 5 minutes |
| 5 | Empty customer phone | Synthetic data lacks phone records | Environment variable fallback | 10 minutes |
| 6 | React hooks order crash | useState after conditional return | Move hooks before early return | 5 minutes |

> **Core takeaway:** Every failure above was caught and fixed without data loss, duplicate charges, or unsafe autonomous actions. The bounded autonomy architecture ensured that when AI or infrastructure failed, the system degraded to human review rather than making incorrect financial decisions.
