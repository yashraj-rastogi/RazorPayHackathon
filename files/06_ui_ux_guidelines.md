# RevGuard — UI/UX Guidelines

## 1. Design goal

The interface should feel like a **financial operations control center**, not a generic AI dashboard.

Priorities:

1. Clarity
2. Trust
3. Decision visibility
4. Financial impact
5. Speed

Avoid decorative AI visualizations that don't help the operator.

## 2. Visual hierarchy

The top of the dashboard should answer:

> "How much money is at risk, how much did we recover, and what needs my attention?"

Recommended order:

```text
Money
↓
Exceptions
↓
Recovery opportunities
↓
Decision details
↓
Audit evidence
```

## 3. Status vocabulary

Use exact system terms consistently.

```text
AUTO
QUEUE_FOR_REVIEW
BLOCKED

PENDING
EXECUTING
UNKNOWN
RECOVERED
FAILED
```

Do not invent multiple synonyms for the same state.

## 4. Color usage

Use color sparingly and semantically.

Suggested semantic meanings:

- Success = recovered / completed
- Warning = review / unknown
- Error = failed
- Neutral = blocked / informational

Do not use color alone to communicate state; pair it with text or icons.

## 5. Trust signals

Every autonomous action should expose:

- why the case qualified
- model confidence when AI was involved
- policy version
- amount threshold
- retry count
- current transaction/payment state
- action result

This reduces the "black-box AI" impression.

## 6. "Why did we act?" component

Example:

```text
WHY WE ACTED

✓ Failure classified as retryable
✓ Confidence: 96%
✓ Amount below auto-action limit
✓ Retry count: 1/3
✓ Customer consent/opt-in present
✓ Current payment state verified
```

## 7. "Why did we not act?" component

Example:

```text
WHY WE DID NOT ACT

✕ Retry limit exceeded
✕ Automatic recovery disabled

Decision:
QUEUE_FOR_REVIEW
```

This should be a first-class UI pattern.

## 8. AI labeling

Whenever Gemini was used, display:

```text
AI-assisted diagnosis
Confidence: 91%
```

Do not imply AI certainty when it does not exist.

## 9. Tables

Optimize for scanning.

Suggested column priority:

1. Amount
2. Cause
3. Decision
4. Status
5. Confidence
6. ID

Keep IDs visually muted.

## 10. Case page

The case detail should read top-to-bottom like an investigation:

```text
What happened?
↓
Why?
↓
What did RevGuard decide?
↓
Was it allowed?
↓
What action happened?
↓
What was the outcome?
```

## 11. Messaging preview

Show customer messages exactly as they will be sent.

Example:

```text
HINGLISH

Hi Rahul, aapka ₹2,499 subscription payment complete nahi ho paaya.
Humne recovery option prepare kiya hai. Aap yahan se payment complete
kar sakte hain: <link>
```

Keep messages:
- short
- clear
- non-coercive
- free from fabricated claims
- consistent with actual action

## 12. Accessibility / usability

Minimum:
- keyboard-friendly buttons
- readable text
- clear focus states
- sufficient contrast
- no information conveyed by color alone
- responsive desktop layout

## 13. Demo optimization

The demo should work at one fixed viewport.

Choose the viewport early, then:
- remove unnecessary scrolling
- keep important metrics above the fold
- make the golden-path case one click away
- pre-seed deterministic demo IDs

## 14. Manual owner actions

Before coding:
- choose typography and component style
- choose one dashboard layout
- decide the fixed demo viewport

During coding:
- do not polish animations before the data flow works
- manually verify every status color/text
- ensure real data powers all dashboard numbers

Before recording:
- hide browser extensions/noisy tabs
- set browser zoom
- use clean demo data
- test the click path three times without interruption
