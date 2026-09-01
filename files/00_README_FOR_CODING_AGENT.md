# RevGuard — Coding Agent Context Pack

## What this repository/spec pack is

This folder contains the full product context for a solo-built hackathon MVP for the Razorpay AI Buildathon.

The coding agent should read these files **before writing code**.

## Read in this order

1. `01_idea.md` — what the product is and is not
2. `02_architecture.md` — technical architecture
3. `03_datamodels.md` — persistence and state
4. `04_userflows.md` — behavior
5. `05_mvp_screens.md` — screens
6. `06_ui_ux_guidelines.md` — design constraints
7. `07_prd_requirements.md` — acceptance criteria
8. `08_ai_prompt_spec.md` — Gemini usage boundaries
9. `09_api_spec.md` — backend contract
10. `10_task_plan_roadmap.md` — build order and manual-owner checkpoints

## Non-negotiable constraints

- Solo developer.
- Four effective days before the September 5 submission.
- One leak type only: failed recurring payments / UPI mandate auto-debits.
- No multi-module Revenue Recovery OS.
- No microservices unless absolutely necessary.
- No unrestricted AI action execution.
- Deterministic financial controls.
- Real synthetic metrics.
- Real failure/recovery story.
- Razorpay Test Mode only.

## Coding-agent operating mode

The coding agent should:

1. Work phase-by-phase.
2. Finish P0 requirements before P1/P2.
3. Avoid adding features not described here.
4. Prefer simple, testable code over framework complexity.
5. Add tests for policy and idempotency logic first.
6. Keep all external providers behind service interfaces.
7. Update documentation when architecture materially changes.
8. Never hard-code credentials.
9. Never hard-code final evaluation metrics.
10. Tell the human developer exactly what manual step must be completed before the next phase.

## Manual-owner protocol

At the end of every major phase, the coding agent should output:

```text
PHASE COMPLETE
1. What was built
2. What was tested automatically
3. What the human must test manually
4. External credentials/actions required
5. Evidence to capture
6. Whether it is safe to proceed
```

The human developer is responsible for:
- creating accounts
- supplying API keys
- verifying third-party dashboards
- testing real test-mode integrations
- approving policy thresholds
- recording real failure behavior
- recording the final pitch
- submitting the hackathon entry

## Definition of Done

A feature is not "done" because it renders.

It is done when:
- backend behavior works
- data persists correctly
- edge cases are handled
- audit trail is recorded
- tests exist for critical logic
- UI reflects real backend data
- the human has completed required manual checks
