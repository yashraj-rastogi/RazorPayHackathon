import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const TABS = [
  { id: 'mission', label: '1. Problem Taste & Mission', icon: '🎯' },
  { id: 'architecture', label: '2. System Architecture', icon: '🏗️' },
  { id: 'ai-judgment', label: '3. AI Judgment & Boundaries', icon: '🧠' },
  { id: 'failure-log', label: '4. Failure Recovery Log', icon: '🛠️' },
  { id: 'evaluator-guide', label: '5. 60-Sec Judge Sandbox', icon: '📱' },
];

export default function Docs() {
  const [activeTab, setActiveTab] = useState('mission');
  const navigate = useNavigate();

  return (
    <div className="docs-page">
      {/* Docs Header */}
      <div className="docs-header">
        <div>
          <div className="docs-badge">RAZORPAY BUILD-FOR-BHARAT // TRACK 03: AI REVENUE RECOVERY</div>
          <h1 className="docs-title">System Architecture & Evaluation Guide</h1>
          <p className="docs-subtitle">
            Comprehensive technical and operational blueprint of RevGuard: Bounded Autonomy, Event-Driven Ingestion, and Multilingual WhatsApp Recovery.
          </p>
        </div>
        <div className="docs-header-actions">
          <button className="btn btn-primary" onClick={() => navigate('/cockpit')}>
            Launch Cockpit ⚡
          </button>
          <button className="btn btn-secondary" onClick={() => navigate('/review')}>
            Review Queue 👁
          </button>
        </div>
      </div>

      {/* Interactive Tabs Bar */}
      <div className="docs-tab-bar">
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={`docs-tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab 1: Problem Taste & Mission */}
      {activeTab === 'mission' && (
        <div className="docs-card fade-in">
          <div className="docs-section-heading">
            <span className="docs-kicker">RUBRIC PILLAR 01</span>
            <h2>Problem Taste: The Indian Subscription Dilemma</h2>
          </div>

          <p className="docs-p">
            In recurring billing ecosystems (SaaS, EdTech, OTT, Insurance, and Memberships), <strong>over 40% of all payment failures are involuntary</strong>.
            The customer did not intend to churn or cancel. Instead, technical friction broke the transaction.
          </p>

          <div className="docs-callout warning">
            <strong>Why India's Recurring Payments Break Differently:</strong>
            <ul>
              <li><strong>RBI e-Mandate Regulations:</strong> Requires AFA (Additional Factor Authentication) for setup and debit notifications that frequently fail due to SMS gateway latencies.</li>
              <li><strong>UPI Autopay Switch Flakiness:</strong> Bank core-banking servers often return transient downtimes (e.g. <code>NPCI_U19</code>) during scheduled midnight batch debits.</li>
              <li><strong>Debit Card Expirations:</strong> In India, debit cards dominate recurring debits; expiry dates silently break renewals without customer awareness.</li>
            </ul>
          </div>

          <h3 style={{ marginTop: '28px' }}>How RevGuard Replaces Delinquency Chasing with Customer Advocacy</h3>
          <p className="docs-p">
            Legacy recovery platforms treat payment failures as debt collection: they spam customers with threatening emails, immediately cut off software access, and trigger automated retries that penalize customers with bank bounce fees. RevGuard flips this paradigm:
          </p>

          <div className="table-container" style={{ margin: '20px 0' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Dimension</th>
                  <th>Legacy Industry Dunning</th>
                  <th>RevGuard Ethical AI Recovery</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Service Continuity</strong></td>
                  <td><span className="badge badge-danger">Immediate Lockout</span> Child blocked from online class; insurance lapses.</td>
                  <td><span className="badge badge-success">Zero Disruption</span> Keeps service active during autonomous recovery window.</td>
                </tr>
                <tr>
                  <td><strong>Tone of Voice</strong></td>
                  <td><span className="badge badge-danger">Threatening / Robotic</span> <em>"Payment failed! Service terminating in 24h!"</em></td>
                  <td><span className="badge badge-success">Empathetic & Polite</span> <em>"Hi Rohit, your bank had a momentary downtime during auto-debit."</em></td>
                </tr>
                <tr>
                  <td><strong>Language Inclusivity</strong></td>
                  <td><span className="badge badge-neutral">English Only</span> Confusing financial jargon that panics non-metro users.</td>
                  <td><span className="badge badge-warning">Native Multilingual</span> WhatsApp allows 1-tap switching between English, Hindi, and Hinglish.</td>
                </tr>
                <tr>
                  <td><strong>Payment Effort</strong></td>
                  <td><span className="badge badge-danger">High Friction</span> Requires logging into web portals, passwords, re-entering details.</td>
                  <td><span className="badge badge-success">10-Second UPI</span> Official Razorpay payment link sent directly to WhatsApp.</td>
                </tr>
                <tr>
                  <td><strong>Customer Consent</strong></td>
                  <td><span className="badge badge-danger">No Exit</span> Relentless retries causing bank bounce penalties.</td>
                  <td><span className="badge badge-success">Strict STOP</span> Inbound <code>STOP</code> reply instantly halts all retries and outreach.</td>
                </tr>
              </tbody>
            </table>
          </div>

          <h3 style={{ marginTop: '28px' }}>The 3-Way Beneficiary Alignment</h3>
          <div className="stakeholders-grid" style={{ marginTop: '16px' }}>
            <div className="stakeholder-card">
              <h4>🏢 The Merchant</h4>
              <p>Protects Monthly Recurring Revenue (MRR) without hiring large manual dunning teams or alienating loyal subscribers.</p>
            </div>
            <div className="stakeholder-card">
              <h4>👤 The Everyday Citizen</h4>
              <p>Enjoys uninterrupted essential services, clear explanations in their native tongue, and zero aggressive harassment.</p>
            </div>
            <div className="stakeholder-card">
              <h4>💳 Razorpay Platform</h4>
              <p>Drives higher payment success rates, expands Autopay volume, and strengthens merchant retention on the Razorpay ecosystem.</p>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: System Architecture */}
      {activeTab === 'architecture' && (
        <div className="docs-card fade-in">
          <div className="docs-section-heading">
            <span className="docs-kicker">RUBRIC PILLAR 02</span>
            <h2>System Architecture & Event-Driven Pipeline</h2>
          </div>

          <p className="docs-p">
            RevGuard is built as enterprise-grade middleware. It runs asynchronously, processes webhooks in milliseconds, and coordinates AI reasoning with deterministic financial APIs.
          </p>

          <div className="arch-diagram-box">
            <pre className="arch-ascii">
              {`┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 REVGUARD SYSTEM ARCHITECTURE                                   │
└────────────────────────────────────────────────────────────────────────────────────────────────┘

  [ Razorpay Webhooks ]           [ Inbound WhatsApp Replies ]
           │                                   │
           ▼                                   ▼
  ┌───────────────────────────────────────────────────────────┐
  │                   FastAPI Core Gateway                    │
  │   • HMAC-SHA256 Signature Verification                    │
  │   • Idempotency Deduplication Key Cache                   │
  │   • Root & Prefix Webhook Delegation                      │
  └─────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
  ┌───────────────────────────────────────────────────────────┐
  │                 Deterministic Policy Engine               │
  │   • Customer Tiering (VIP / High / Standard)              │
  │   • Recovery SLA Deadline Calculation                     │
  │   • Confidence Gating: Autonomous vs. Operator Review     │
  └─────────────────────────────┬─────────────────────────────┘
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
  ┌─────────────────────────────┐┌────────────────────────────┐
  │   Autonomous Path (>=0.85)  ││  Human Review Queue (<0.85)│
  │   Instant Dispatch          ││  Audited Manual Oversight  │
  └──────────────┬──────────────┘└─────────────┬──────────────┘
                 │                             │
                 └──────────────┬──────────────┘
                                ▼
  ┌───────────────────────────────────────────────────────────┐
  │             Gemini 2.5 Cognitive Layer                    │
  │   • Diagnostic Extraction (NPCI & Gateway code mapping)   │
  │   • Empathetic Tone Modulation                            │
  │   • Multi-Language Variant Synthesis (EN, HI, Hinglish)   │
  └─────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
  ┌───────────────────────────────────────────────────────────┐
  │              Omnichannel Recovery Engine                  │
  │   • Razorpay API: Tokenized Payment Link Creation         │
  │   • Twilio WhatsApp Sandbox: Interactive Outbound Dispatch│
  │   • TwiML Synchronous Response Engine                     │
  └─────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
  ┌───────────────────────────────────────────────────────────┐
  │              Firestore State & Audit Ledger               │
  │   • Case Lifecycle (DETECTED -> RECOVERED / ABANDONED)   │
  │   • Real-Time Event Audit History                         │
  │   • Aggregated Financial Performance Metrics              │
  └───────────────────────────────────────────────────────────┘`}
            </pre>
          </div>

          <h3 style={{ marginTop: '24px' }}>Core Engineering Standards</h3>
          <div className="feature-checklist">
            <div className="docs-check-item">
              <span className="check-icon">✓</span>
              <div>
                <strong>HMAC Signature Verification:</strong> Every inbound webhook from Razorpay is cryptographically verified using secret key digests before processing.
              </div>
            </div>
            <div className="docs-check-item">
              <span className="check-icon">✓</span>
              <div>
                <strong>Strict Idempotency:</strong> Webhooks are hashed by event ID and payload signature to prevent duplicate charges or repetitive messages.
              </div>
            </div>
            <div className="docs-check-item">
              <span className="check-icon">✓</span>
              <div>
                <strong>48/48 Automated Tests Passing:</strong> The complete test suite exercises policy rules, risk classification, webhook handling, and Twilio dispatch with zero mock failures.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: AI Judgment & Boundaries */}
      {activeTab === 'ai-judgment' && (
        <div className="docs-card fade-in">
          <div className="docs-section-heading">
            <span className="docs-kicker">RUBRIC PILLAR 03</span>
            <h2>AI Judgment: Bounded Autonomy in Financial Systems</h2>
          </div>

          <p className="docs-p">
            Hackathons frequently suffer from "AI overreach" — attempting to let an LLM execute database writes, financial arithmetic, and policy limits. In financial engineering, this is catastrophic. RevGuard implements a strict <strong>Bounded Autonomy</strong> architecture.
          </p>

          <div className="table-container" style={{ margin: '20px 0' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Component / Capability</th>
                  <th>Execution Engine</th>
                  <th>Architectural Justification</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Cryptic Error Code Translation</strong></td>
                  <td><span className="badge badge-accent">Gemini 2.5 Pro</span></td>
                  <td>Banks return inconsistent codes (<code>U19</code>, <code>ZA</code>, <code>U28</code>). LLM probabilistic reasoning maps them to human-readable causes seamlessly.</td>
                </tr>
                <tr>
                  <td><strong>Empathetic Tone & Framing</strong></td>
                  <td><span className="badge badge-accent">Gemini 2.5 Pro</span></td>
                  <td>Contextual empathy prevents subscriber panic while encouraging timely resolution. LLMs adapt tone based on customer tier and invoice urgency.</td>
                </tr>
                <tr>
                  <td><strong>Hindi & Hinglish Localization</strong></td>
                  <td><span className="badge badge-accent">Gemini 2.5 Pro</span></td>
                  <td>Mechanical translators fail on conversational Indian billing terms. LLM produces natural phrasing like <em>"Aapka monthly subscription auto-debit complete nahi ho paya."</em></td>
                </tr>
                <tr>
                  <td><strong>Inbound Reply Intent Analysis</strong></td>
                  <td><span className="badge badge-accent">Gemini 2.5 Pro</span></td>
                  <td>Detects whether unstructured replies represent a payment confirmation, a dispute, or a question before falling back to manual queue.</td>
                </tr>
                <tr>
                  <td><strong>Invoice Calculation & Decimals</strong></td>
                  <td><span className="badge badge-neutral">Deterministic Python</span></td>
                  <td><strong>Never use an LLM for math.</strong> Precision currency arithmetic (Paisa to Rupee conversion) is strictly hard-coded.</td>
                </tr>
                <tr>
                  <td><strong>Payment Link Token Generation</strong></td>
                  <td><span className="badge badge-neutral">Razorpay Official SDK</span></td>
                  <td>Checkout links must be cryptographically generated via Razorpay's verified API endpoints.</td>
                </tr>
                <tr>
                  <td><strong>Retry Limits & Cooldowns</strong></td>
                  <td><span className="badge badge-neutral">Deterministic Policy</span></td>
                  <td>Hard bounds (max 3 retries, mandatory 48-hour cooldowns) prevent spamming customers or triggering bank penalties.</td>
                </tr>
                <tr>
                  <td><strong>Legal Opt-Out (`STOP`)</strong></td>
                  <td><span className="badge badge-danger">Hard Code Database Lock</span></td>
                  <td>When a customer replies <code>STOP</code>, an irreversible database flag suppresses all outreach immediately without LLM interpretation.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 4: Failure Recovery Log */}
      {activeTab === 'failure-log' && (
        <div className="docs-card fade-in">
          <div className="docs-section-heading">
            <span className="docs-kicker">RUBRIC PILLAR 04</span>
            <h2>Failure Recovery: What Broke & What We Did About It</h2>
          </div>

          <p className="docs-p">
            Real engineering is proven in how systems withstand production edge cases. Here are the 7 actual engineering failures encountered and resolved during RevGuard's development:
          </p>

          <div className="failure-log-list">
            <div className="failure-item">
              <div className="failure-num">01</div>
              <div className="failure-details">
                <h4>Gemini Markdown Fence Stripping in JSON Output</h4>
                <p className="failure-cause"><strong>What Broke:</strong> LLM occasionally returned JSON wrapped in <code>```json ... ```</code> code blocks, causing standard <code>json.loads()</code> to crash.</p>
                <p className="failure-fix"><strong>Recovery Engineering:</strong> Implemented robust regex stripping and schema validation fallbacks, ensuring deterministic deserialization under all prompt outputs.</p>
              </div>
            </div>

            <div className="failure-item">
              <div className="failure-num">02</div>
              <div className="failure-details">
                <h4>Missing Customer Contact in Razorpay Webhooks</h4>
                <p className="failure-cause"><strong>What Broke:</strong> Certain subscription failure webhooks did not include top-level customer phone numbers in the payload.</p>
                <p className="failure-fix"><strong>Recovery Engineering:</strong> Added multi-tiered resolution: inspects nested customer entities, falls back to linked payment records, and defaults to secure customer portal lookup.</p>
              </div>
            </div>

            <div className="failure-item">
              <div className="failure-num">03</div>
              <div className="failure-details">
                <h4>Firestore Client Disconnect on Long-Lived Worker</h4>
                <p className="failure-cause"><strong>What Broke:</strong> Google Cloud Firestore gRPC channels experienced silent keep-alive timeouts after prolonged idle periods.</p>
                <p className="failure-fix"><strong>Recovery Engineering:</strong> Implemented automatic exponential backoff retry wrappers and dynamic client reconnection on transient gRPC exceptions.</p>
              </div>
            </div>

            <div className="failure-item">
              <div className="failure-num">04</div>
              <div className="failure-details">
                <h4>Out-of-Order Webhook Delivery Race Conditions</h4>
                <p className="failure-cause"><strong>What Broke:</strong> A <code>payment.captured</code> webhook arrived before the corresponding <code>subscription.charged_failed</code> case finished creation.</p>
                <p className="failure-fix"><strong>Recovery Engineering:</strong> Implemented atomic document locking and upside-down state reconciliations: if captured first, the case initializes directly as <code>RECOVERED</code>.</p>
              </div>
            </div>

            <div className="failure-item">
              <div className="failure-num">05</div>
              <div className="failure-details">
                <h4>Twilio WhatsApp Sandbox Unregistered Number Rejection</h4>
                <p className="failure-cause"><strong>What Broke:</strong> Evaluating judges attempting to test on personal phones received Twilio delivery errors because their number had not joined the sandbox.</p>
                <p className="failure-fix"><strong>Recovery Engineering:</strong> Added in-app interactive modal with clear sandbox opt-in instructions and custom judge phone number override fields.</p>
              </div>
            </div>

            <div className="failure-item">
              <div className="failure-num">06</div>
              <div className="failure-details">
                <h4>Inbound Language Switching Reply Ambiguity</h4>
                <p className="failure-cause"><strong>What Broke:</strong> Customers replied with conversational text like <em>"hindi me bhejo"</em> or <em>"option 2 please"</em> instead of pure numbers.</p>
                <p className="failure-fix"><strong>Recovery Engineering:</strong> Upgraded inbound reply handler with multi-stage matching: exact number check $\to$ conversational regex $\to$ Gemini intent classification.</p>
              </div>
            </div>

            <div className="failure-item">
              <div className="failure-num">07</div>
              <div className="failure-details">
                <h4>Twilio Webhook Root 405 Path Delegation & TwiML Delivery</h4>
                <p className="failure-cause"><strong>What Broke:</strong> Twilio sandbox webhooks pointed to the ngrok root URL (<code>POST /</code>) instead of the deep subpath, causing a <code>405 Method Not Allowed</code> error.</p>
                <p className="failure-fix"><strong>Recovery Engineering:</strong> Added root <code>POST /</code> delegation in FastAPI and returned synchronous TwiML XML <code>&lt;Response&gt;&lt;Message&gt;...&lt;/Message&gt;&lt;/Response&gt;</code> for immediate WhatsApp delivery.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 5: 60-Second Evaluator Guide */}
      {activeTab === 'evaluator-guide' && (
        <div className="docs-card fade-in">
          <div className="docs-section-heading">
            <span className="docs-kicker">INTERACTIVE TESTING</span>
            <h2>Judge Evaluation Sandbox: Live 60-Second Test</h2>
          </div>

          <p className="docs-p">
            Follow this 3-step walkthrough to experience RevGuard's live end-to-end recovery on your own mobile device.
          </p>

          <div className="judge-sandbox-steps">
            <div className="sandbox-card">
              <div className="sandbox-badge">STEP 1</div>
              <h3>Join Twilio WhatsApp Sandbox (One-Time)</h3>
              <p>On your mobile phone, open WhatsApp and send the following message to Twilio's verified sandbox number:</p>
              <div className="code-box">
                <div><strong>To:</strong> +1 415 523 8886</div>
                <div><strong>Message:</strong> <code>join pile-cup</code></div>
              </div>
              <p className="text-muted" style={{ fontSize: '13px', marginTop: '8px' }}>
                You will immediately receive a confirmation: <em>"You are all set! The sandbox keyword has been joined."</em>
              </p>
            </div>

            <div className="sandbox-card">
              <div className="sandbox-badge">STEP 2</div>
              <h3>Trigger Case Review from the Dashboard</h3>
              <p>Go to the <strong>Review Queue</strong> or <strong>Cockpit</strong> in this app:</p>
              <ol style={{ paddingLeft: '20px', lineHeight: '1.8' }}>
                <li>Click on any case marked <span className="badge badge-warning">QUEUE_FOR_REVIEW</span> or <em>Review Case</em>.</li>
                <li>In the recovery review modal, enter your WhatsApp phone number (e.g. <code>+919876543210</code>).</li>
                <li>Click <strong>Approve & Dispatch</strong>.</li>
              </ol>
            </div>

            <div className="sandbox-card">
              <div className="sandbox-badge">STEP 3</div>
              <h3>Receive Link, Switch Language & Verify Payment</h3>
              <p>Watch your WhatsApp conversation:</p>
              <ol style={{ paddingLeft: '20px', lineHeight: '1.8' }}>
                <li>You will instantly receive the diagnostic recovery notification with an official Razorpay payment link.</li>
                <li>Reply with <code>2</code> on WhatsApp to test Hinglish language switching. You will immediately receive the translated recovery note.</li>
                <li>Tap the Razorpay link to open the test checkout. Complete a test payment using test UPI or Netbanking.</li>
                <li>Watch the Cockpit automatically update the case state to <span className="badge badge-success">RECOVERED</span>.</li>
              </ol>
            </div>
          </div>

          <div style={{ marginTop: '24px', display: 'flex', gap: '12px' }}>
            <button className="btn btn-primary" onClick={() => navigate('/review')}>
              Go to Review Queue Now 👁
            </button>
            <button className="btn btn-secondary" onClick={() => navigate('/cockpit')}>
              View Live Cockpit ⚡
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
