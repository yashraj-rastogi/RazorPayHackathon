# ⚡ RevGuard — 5-Minute Pitch & Demo Script
### Razorpay Build-for-Bharat 2026 // Track 03: AI Revenue Recovery

> **Target time: 4 minutes 30 seconds | Hard limit: 5:00**

---

## 🖥️ SETUP BEFORE RECORDING (Do this first!)

Open these browser tabs **in order** before you hit record:

| Tab | URL | Page |
|-----|-----|------|
| Tab 1 | `http://localhost:5173/` | Landing Page |
| Tab 2 | `http://localhost:5173/cockpit` | Live Cockpit Dashboard |
| Tab 3 | `http://localhost:5173/review` | Review Queue |
| Tab 4 | `http://localhost:5173/docs` | Docs (AI Judgment tab open) |

**Phone:** WhatsApp open, already joined Twilio sandbox
(`join breakfast-mountain` → `+1 415 523 8886`)

---

## 🎬 SEGMENT 1 — THE PROBLEM [0:00–0:40]

> 📺 **Show:** Tab 1 — Landing Page.
> Point cursor at the headline and scroll slowly to the comparison section.

**SAY:**
> "Every month, across India's subscription economy — SaaS, EdTech, OTT, insurance —
> millions of payment failures happen that customers never caused.
> A bank was down for 10 minutes. A UPI mandate hit an RBI regulation glitch.
> A debit card expired silently.
>
> These are involuntary failures. But traditional platforms treat every failure
> the same way: cut off the service, send a threatening email, and retry blindly.
>
> That costs Indian merchants 15 to 20% of their recurring revenue —
> and it destroys customer trust. RevGuard is our answer to that."

---

## 🎬 SEGMENT 2 — WHAT REVGUARD DOES [0:40–1:30]

> 📺 **Show:** Click "Launch Cockpit ⚡" → Tab 2.
> Point cursor at the KPI cards (Revenue at Risk, Revenue Recovered, Auto Actions, Review Queue).

**SAY:**
> "RevGuard is intelligent B2B middleware that sits directly on top
> of Razorpay's webhook infrastructure.
>
> When a subscription debit fails, Razorpay sends us a real-time signal.
> We verify it cryptographically, check idempotency so nothing is processed twice,
> and run it through our Policy Engine.
>
> For standard, low-risk failures, the system acts fully autonomously
> — in under 45 seconds.
> Gemini 2.5 Pro reads the cryptic bank error code and turns it into
> a clear, empathetic explanation.
>
> Then our system deterministically generates an official Razorpay payment link
> and sends it to the customer's WhatsApp —
> no login required, no bank portal, just one tap to pay."

---

## 🎬 SEGMENT 3 — LIVE DEMO: REVIEW & DISPATCH [1:30–2:30]

> 📺 **Show:** Switch to Tab 3 — Review Queue.
> Click "Review Case" on any queued case.
> Show the modal with the phone field.
> Enter YOUR WhatsApp number.
> Click "Approve & Dispatch".
> Show your phone screen with WhatsApp receiving the message.
> Reply with **2** on your phone.
> Show the Hinglish reply arriving instantly.

**SAY:**
> "Here's where it gets interesting. Not everything should be automated.
>
> If a case has a high invoice amount, or the AI is less than 85% confident
> in its diagnosis, RevGuard restrains itself.
> It routes the case here — to a human operator review queue —
> before taking any action.
>
> I'll approve this case now and dispatch the Razorpay recovery link
> to my own phone so you can watch it live.
>
> [CLICK: Approve & Dispatch]
>
> And here it is — on my phone, a WhatsApp message with the official
> Razorpay payment link.
>
> Now watch: I reply with the number 2.
>
> [REPLY: 2 on phone]
>
> Instantly — our webhook responds in Hinglish.
> Because in India, customers trust their native language
> more than banking jargon.
>
> When they tap the link and pay, Razorpay fires a payment.captured webhook,
> and that case automatically closes as Recovered in our dashboard.
> Zero manual work."

---

## 🎬 SEGMENT 4 — AI JUDGMENT: BOUNDED AUTONOMY [2:30–3:20]

> 📺 **Show:** Switch to Tab 4 — Docs.
> Click "3. AI Judgment & Boundaries" tab.
> Point cursor slowly at the two-column table.

**SAY:**
> "The third judging criterion asks: did you use AI in the right places,
> and did you know where NOT to use it?
>
> Our answer is what we call Bounded Autonomy.
>
> We use Gemini 2.5 Pro for four things:
> diagnosing cryptic bank error codes,
> calibrating empathetic tone,
> generating authentic Hindi and Hinglish phrasing,
> and detecting intent from inbound customer replies.
>
> But AI is strictly forbidden from:
> calculating rupee amounts,
> generating Razorpay checkout tokens,
> enforcing retry limits,
> and processing customer opt-outs.
>
> If a customer texts STOP — a hard database lock kicks in immediately.
> No AI interprets that. No retry will ever go through again.
> That is a non-negotiable rule.
>
> In financial systems, AI should handle ambiguity.
> Deterministic code should handle consequences."

---

## 🎬 SEGMENT 5 — FAILURE RECOVERY [3:20–4:00]

> 📺 **Show:** In Docs, click "4. Failure Recovery Log" tab.
> Point cursor briefly at Failure 01 and Failure 07.

**SAY:**
> "The fourth criterion: what broke, and what did you do about it?
>
> We documented every real engineering failure. Two stand out.
>
> First — Gemini occasionally returned valid JSON wrapped in markdown
> code fences, crashing our parser.
> We added automatic text sanitization and a fallback schema.
> If the AI ever fails or times out, the case routes to human review
> instead of crashing.
>
> Second — during live phone testing, Twilio sandbox webhooks were
> hitting the wrong URL path, throwing a 405 error.
> Customer language-switch replies were getting lost.
> We added root-level request delegation in FastAPI
> and upgraded to synchronous TwiML XML responses —
> so the translated WhatsApp reply arrives under one second.
>
> Every failure we hit made the system more resilient.
> And none of them ever caused a duplicate charge or an unsafe action —
> because our bounded autonomy architecture degrades to human review,
> never to guesswork."

---

## 🎬 SEGMENT 6 — IMPACT & CLOSE [4:00–4:30]

> 📺 **Show:** Switch back to Tab 1 — Landing Page.
> Point cursor at the 4 metric chips in the Hero section.
> (₹4.82L Recovered, 87.4% Recovery Rate, <45s SLA, 40%+ Churn Rescued)

**SAY:**
> "RevGuard is backed by 48 passing automated tests,
> a real Razorpay integration, and real Twilio WhatsApp delivery.
>
> The result:
> Merchants rescue at-risk recurring revenue.
> Everyday Indians keep their services running without being harassed.
> And Razorpay gets higher payment success rates and deeper merchant loyalty.
>
> We've built it. It runs. You just watched it work live.
>
> Thank you — and we invite the judges to test it directly
> using the live sandbox in our in-app documentation.
> The instructions are one click away."

---

## ⏱️ TIME MAP

| Segment | What It Covers | Duration |
|---------|---------------|----------|
| 1 | The Problem | 0:40 |
| 2 | What RevGuard Does | 0:50 |
| 3 | **Live Demo** — WhatsApp Recovery | 1:00 |
| 4 | AI Judgment & Bounded Autonomy | 0:50 |
| 5 | Failure Recovery Log | 0:40 |
| 6 | Impact & Close | 0:30 |
| **TOTAL** | | **~4:30** |

---

## ✅ 4 JUDGING CRITERIA — WHERE THEY ARE COVERED

| Criterion | Covered In |
|-----------|-----------|
| **Problem Taste** — Did you pick something that matters? | Segment 1 + Segment 6 |
| **Build Quality** — Does it run, is it structured, would you trust it? | Segment 2 + Segment 3 |
| **AI Judgment** — Right tool in the right place | Segment 4 |
| **Failure Recovery** — What broke, what you did | Segment 5 |

---

## 💡 3 THINGS THAT WILL MAKE YOUR VIDEO WIN

1. **Show the real phone.**
   When WhatsApp receives the message and you reply `2` for Hinglish,
   that live physical proof is what judges remember above everything else.

2. **Speak at your normal conversation pace.**
   If you rush, it sounds nervous.
   Slow down naturally on the key terms:
   *Bounded Autonomy*, *Failure Recovery*, *Involuntary Churn*.

3. **Move your cursor intentionally.**
   Every time you name something on screen, point your cursor to it.
   It keeps the judge's eyes exactly where you want them.

---

*RevGuard // Razorpay Build-for-Bharat 2026 // Track 03: AI Revenue Recovery*
*Bounded Autonomy Engine v1.0 // 48 Passing Tests // Real Razorpay + Twilio Integration*
