# RevGuard: Business, Consumer & Data Architecture Guide

> **Ecosystem Positioning, Consumer Impact, and Webhook Data Sourcing for Evaluators & Integrators**

---

## 1. Executive Summary & Ecosystem Positioning

### What is RevGuard?
RevGuard is **B2B intelligent middleware for merchants running recurring billing and UPI Autopay on Razorpay**. 

It is not a direct-to-consumer application that end-users download. Instead, businesses (SaaS companies, OTT streaming platforms, EdTech providers, insurance carriers, fitness memberships, and utility providers) integrate RevGuard into their Razorpay billing stack. RevGuard operates silently in the background on behalf of the merchant as an intelligent retention, diagnosis, and ethical recovery controller.

```
┌─────────────────────────────────────────────────────────┐
│                     END CONSUMER                        │
│          (Student, Subscriber, Policyholder)            │
└────────────────────────────┬────────────────────────────┘
                             │ Uses App / Subscribes
                             ▼
┌─────────────────────────────────────────────────────────┐
│                   MERCHANT PLATFORM                     │
│              (EdTech / OTT / SaaS / Gym)                │
└────────────────────────────┬────────────────────────────┘
                             │ Recurring Billing / Mandates
                             ▼
┌─────────────────────────────────────────────────────────┐
│                  RAZORPAY PAYMENT GATEWAY               │
│        (UPI Autopay / Standing Mandates / Cards)        │
└────────────────────────────┬────────────────────────────┘
                             │ Real-Time Webhooks
                             ▼
┌─────────────────────────────────────────────────────────┐
│                  REVGUARD MIDDLEWARE                    │
│   • Ingests Failed Debits    • Deterministic Policy     │
│   • AI Diagnosis (Gemini)    • Razorpay Links + Twilio  │
└─────────────────────────────────────────────────────────┘
```

---

## 2. How RevGuard Helps the "Everyday Person" (Consumer Impact)

In recurring payments, over **40% of payment failures are involuntary** — meaning the user did not intend to churn or cancel. Their bank's UPI switch was temporarily down, their debit card expired, or a monthly mandate failed silently.

Traditional recovery treats every failure as a delinquency. RevGuard reimagines payment recovery as **customer advocacy**.

### The Consumer Comparison

| Dimension | Legacy Recovery (Industry Default) | RevGuard Ethical AI Recovery |
|---|---|---|
| **Service Continuity** | **Immediate Suspension:** The user's child is locked out of their EdTech class, or their health insurance lapses without warning. | **Zero Service Disruption:** RevGuard detects the failure and opens an automated recovery window before service termination. |
| **Communication Tone** | **Aggressive & Threatening:** Robotic spam emails and threatening collection calls: *"Your payment has failed! Your account will be terminated immediately!"* | **Empathetic & Transparent:** Gemini AI drafts polite, transparent outreach: *"Hi Rohit, your bank had a temporary downtime during your monthly auto-debit. Here is a secure link to renew."* |
| **Language & Inclusivity** | **Rigid English Templates:** Confusing banking terminology that creates panic or distrust among tier-2/tier-3 users. | **Native Multilingual (EN, Hindi, Hinglish):** Adapts to customer preference, explaining issues clearly without financial jargon. |
| **Payment Friction** | **High Friction:** Users must remember passwords, log into web portals, navigate to complex billing settings, and re-type card details. | **10-Second WhatsApp Pay:** Delivers an official, verified Razorpay Payment Link directly to WhatsApp for instant 1-click payment via Google Pay, PhonePe, or UPI. |
| **Consumer Dignity & Consent** | **Spam with No Exit:** Relentless automated retries that hit customer bank accounts and trigger bank bounce charges. | **Absolute Opt-Out (`STOP`):** Inbound WhatsApp webhook instantly honors customer opt-outs, blocking further outreach and suppressing retries. |

---

## 3. Data Sourcing: Where Does Failed Payment Data Come From?

RevGuard does not require manual data entry. Telemetry is streamed **in real time directly from Razorpay's Core Gateway via Webhooks**.

### The Trigger Flow
1. **Scheduled Auto-Debit Execution:**  
   On the billing anniversary, Razorpay attempts to execute an auto-debit against the customer's registered UPI Mandate or Card Token.
2. **Gateway Failure:**  
   If the issuing bank rejects the transaction (e.g., bank switch timeout, mandate balance insufficient, or technical glitch), Razorpay's gateway captures the failure.
3. **Automated Webhook Dispatch:**  
   Razorpay immediately fires an HTTP POST webhook to RevGuard's ingestion endpoint:
   ```
   POST /api/v1/webhooks/razorpay
   ```

### Real Webhook Ingestion Payload (Sample)
```json
{
  "entity": "event",
  "account_id": "acc_mock_merchant",
  "event": "payment.failed",
  "contains": ["payment"],
  "payload": {
    "payment": {
      "entity": {
        "id": "pay_O7d812hklm98",
        "amount": 49900,
        "currency": "INR",
        "status": "failed",
        "method": "upi",
        "error_code": "BAD_REQUEST_ERROR",
        "error_description": "Payment was declined by the issuing bank due to temporary technical failure",
        "error_source": "bank_system",
        "error_step": "payment_authorization",
        "error_reason": "payment_failed",
        "contact": "+919876543210",
        "email": "customer@example.com",
        "notes": {
          "subscription_id": "sub_9812497124",
          "retry_count": "1"
        }
      }
    }
  }
}
```

### Key Data Points Ingested by RevGuard
- **Financial Value:** `amount` (stored strictly as integer paise, e.g. `49900` = ₹499.00).
- **Failure Code & Error Description:** The exact technical reason returned by the bank switch.
- **Retry Count:** Number of automated attempts already made by the gateway.
- **Subscription & Customer IDs:** Correlating the incident to the customer's billing relationship.

---

## 4. Contact Sourcing: How Do We Get the Customer's WhatsApp Number?

In India's subscription payments ecosystem, **the customer's mobile number is already captured during initial signup and checkout**:

1. **Merchant User Profile:**  
   When a user signs up on the merchant's application, they authenticate via mobile OTP.
2. **Mandate Registration Object:**  
   Under RBI's e-mandate framework for recurring payments, every mandate registration requires a valid customer phone number (`contact`) and email address.
3. **Webhook Payload Delivery:**  
   When Razorpay dispatches the `payment.failed` or `subscription.charged_failed` webhook, the customer's registered E.164 phone number (`+9198XXXXXXXX`) is included directly inside the payload's `contact` field.
4. **WhatsApp Opt-In Compliance:**  
   During initial checkout, merchants include the standard regulatory opt-in checkbox:
   > *"Receive billing receipts and subscription renewal notifications on WhatsApp."*  
   This establishes `whatsapp_opt_in: true` in the customer record.

---

## 5. End-to-End Recovery Lifecycle

```
[Customer Subscription Auto-Debit Fails at Bank]
                       │
                       ▼ (Razorpay Webhook: payment.failed)
     [RevGuard Layer A: Ingestion & Idempotency Check]
                       │
                       ▼
     [RevGuard Layer B: Root Cause Diagnosis (Deterministic / Gemini)]
                       │
                       ▼
     [RevGuard Layer C: Priority Scoring (amount × recovery_prob)]
                       │
                       ▼
     [RevGuard Layer D: Deterministic Policy Engine Verification]
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
 [Decision: AUTO]            [Decision: QUEUE_FOR_REVIEW]
       │                               │
       │                               ▼
       │                    (Held in Operator Review Cockpit)
       │                               │
       │                    [Operator Clicks "Approve"]
       │                               │
       └───────────────┬───────────────┘
                       │
                       ▼
  [RevGuard Layer E: Mint Razorpay Payment Link (rzp.io/i/...)]
                       │
                       ▼
  [RevGuard Layer E: Generate Localized WhatsApp Copy (Gemini/Fallback)]
                       │
                       ▼ (Dispatched via Twilio WhatsApp API)
  [Customer Receives Polite WhatsApp Message with 1-Click Pay Link]
                       │
                       ▼ (Customer pays via UPI / Google Pay / PhonePe)
  [Razorpay Webhook: payment_link.paid received by RevGuard]
                       │
                       ▼
  [Case Marked RECOVERED · ARR Saved Credited · Audit Certificate Generated]
```

---

## 6. Summary for Hackathon Judges

1. **Not a Speculative Chatbot:** RevGuard does not let LLMs handle money, modify prices, or trigger unauthorized debits. AI only classifies ambiguity and writes polite text; deterministic code enforces policies.
2. **B2B Infrastructure:** Built specifically as an enterprise-grade middleware component that plugs directly into the Razorpay merchant ecosystem.
3. **Consumer-Centric Ethics:** Protects subscribers from unfair service terminations, avoids aggressive debt-collection spam, and delivers 1-click WhatsApp resolution.
