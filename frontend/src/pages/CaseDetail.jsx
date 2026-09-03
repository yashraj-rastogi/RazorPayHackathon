import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api, formatRupees, formatDate, policyBadgeClass, statusBadgeClass, confidenceColor } from '../api';

function PolicyChecklist({ policy }) {
  if (!policy) return null;
  const reasons = policy.reasons || [];
  const isAuto = policy.decision === 'AUTO';
  const isBlocked = policy.decision === 'BLOCKED';

  return (
    <div>
      <div className="section-title">
        <span>🛡</span>
        <span>
          {isAuto
            ? 'Deterministic Verification: Pass Criteria'
            : isBlocked
            ? 'Safety Interlock: Block Triggers'
            : 'Human Escalate: Review Thresholds'}
        </span>
      </div>
      <div className="checklist">
        {reasons.map((r, i) => (
          <div
            key={i}
            className={`checklist-item ${isAuto ? 'pass' : isBlocked ? 'fail' : 'neutral'}`}
          >
            <div className="check-icon-box">
              {isAuto ? '✓' : isBlocked ? '✗' : '!'}
            </div>
            <span style={{ fontWeight: '500' }}>{r}</span>
          </div>
        ))}
        {policy.block_reason && (
          <div className="checklist-item fail">
            <div className="check-icon-box">✗</div>
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '700' }}>
              SAFETY INTERLOCK CODE: {policy.block_reason}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

function AuditTimeline({ audit }) {
  const items = audit?.events || [];
  if (!items.length) {
    return (
      <div className="empty-state">
        <p style={{ fontFamily: 'var(--font-mono)' }}>NO AUDIT TELEMETRY REGISTERED YET.</p>
      </div>
    );
  }

  const actorClass = (actor) => ({
    system: 'timeline-dot-system',
    human: 'timeline-dot-human',
    webhook: 'timeline-dot-webhook',
  }[actor] || 'timeline-dot-system');

  const actorIcon = (actor) => ({
    system: '⚙',
    human: '👤',
    webhook: '🔗',
  }[actor] || '⚙');

  return (
    <div className="timeline">
      {items.map((item, i) => (
        <div key={i} className="timeline-item">
          <div className={`timeline-dot ${actorClass(item.actor)}`}>
            {actorIcon(item.actor)}
          </div>
          <div className="timeline-content">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
              <div className="timeline-action">{item.action}</div>
              <div className="timeline-meta">{formatDate(item.timestamp)}</div>
            </div>
            <div className="timeline-meta" style={{ marginTop: '2px' }}>
              STAGE: {item.stage?.toUpperCase()} // ACTOR: {item.actor?.toUpperCase()}
            </div>
            {item.details && Object.keys(item.details).length > 0 && (
              <pre style={{
                marginTop: '8px',
                padding: '8px 12px',
                backgroundColor: 'var(--color-bg-elevated)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-sm)',
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                color: 'var(--color-dark)',
                overflowX: 'auto',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-all',
              }}>
                {JSON.stringify(item.details, null, 2)}
              </pre>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function MessagePreview({ caseId }) {
  const [msg, setMsg] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getCaseMessage(caseId)
      .then(setMsg)
      .catch(() => setMsg(null))
      .finally(() => setLoading(false));
  }, [caseId]);

  if (loading) {
    return (
      <div className="loading" style={{ padding: '24px 0' }}>
        <div className="spinner" />
        <span>FETCHING OUTREACH PAYLOAD...</span>
      </div>
    );
  }

  if (!msg) {
    return (
      <div className="empty-state">
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: '13px' }}>
          NO OUTREACH DISPATCHED YET. TRIGGER RECOVERY TO GENERATE SECURE LINK.
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="message-bubble">
        <div style={{
          position: 'absolute',
          top: '-12px',
          left: '16px',
          backgroundColor: 'var(--color-accent)',
          border: 'var(--border-thin)',
          padding: '2px 8px',
          fontFamily: 'var(--font-mono)',
          fontSize: '10px',
          fontWeight: '800',
          textTransform: 'uppercase',
          letterSpacing: '0.05em'
        }}>
          SECURE OUTREACH PAYLOAD
        </div>
        <p style={{ marginTop: 6 }}>{msg.message}</p>
      </div>
      <div className="message-meta">
        <span>🌐 LANGUAGE: {msg.language?.toUpperCase()}</span>
        <span>🎨 TONE: {msg.tone?.toUpperCase()}</span>
        <span>📋 PROMPT: {msg.prompt_version}</span>
        <span>📤 DISPATCH: {msg.sent ? `SENT AT ${formatDate(msg.sent_at)}` : 'PENDING'}</span>
      </div>
    </div>
  );
}

export default function CaseDetail() {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const [detail, setDetail] = useState(null);
  const [audit, setAudit] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  const load = () => {
    setLoading(true);
    api.getCase(caseId)
      .then(d => {
        setDetail(d);
        api.getCaseAudit(caseId)
          .then(setAudit)
          .catch(() => setAudit({ events: [] }));
      })
      .catch(err => {
        console.error(err);
        setDetail(null);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [caseId]);

  const handleRecover = async () => {
    setActionMsg('EXECUTING ACTION VIA RAZORPAY...');
    try {
      const r = await api.recoverCase(caseId);
      setActionMsg(`✓ PAYMENT LINK CREATED: ${r.recovery_url || r.provider_reference}`);
      load();
    } catch (e) {
      setActionMsg('✗ ' + e.message);
    }
  };

  const handleApprove = async () => {
    setActionMsg('APPROVING INCIDENT FOR RECOVERY...');
    try {
      await api.approveCase(caseId);
      setActionMsg('✓ APPROVED & DISPATCHED');
      load();
    } catch (e) {
      setActionMsg('✗ ' + e.message);
    }
  };

  const handleReject = async () => {
    setActionMsg('REJECTING INCIDENT...');
    try {
      await api.rejectCase(caseId, 'Manually rejected by operator');
      setActionMsg('✓ INCIDENT CLOSED');
      load();
    } catch (e) {
      setActionMsg('✗ ' + e.message);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" />
        <span>READING TELEMETRY FOR {caseId}...</span>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="card">
        <div className="empty-state">
          <p>CASE RECORD NOT LOCATED IN REPOSITORY</p>
        </div>
      </div>
    );
  }

  const c = detail.case || {};
  const event = detail.event || {};
  const diag = c.diagnosis || {};
  const policy = c.policy || {};
  const conf = diag.confidence || 0;

  const TABS = [
    { key: 'overview', label: 'Telemetric Overview' },
    { key: 'audit', label: `Audit Trail (${audit?.events?.length || 0})` },
    { key: 'message', label: 'Customer Outreach' },
  ];

  return (
    <div>
      {/* Top Header & Actions Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16, marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button className="btn btn-ghost" onClick={() => navigate('/cases')}>
            ← BACK TO LEDGER
          </button>
          <div>
            <h2 style={{ fontSize: '20px' }}>Incident Telemetry</h2>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', fontWeight: '700', color: 'var(--color-dark)' }}>
              REF: {c.case_id}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          {actionMsg && (
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              fontWeight: '700',
              padding: '6px 12px',
              border: '2px solid var(--color-border)',
              backgroundColor: actionMsg.startsWith('✓') ? 'rgba(76, 175, 80, 0.15)' : 'rgba(229, 57, 53, 0.15)',
              color: actionMsg.startsWith('✓') ? '#1B5E20' : '#B71C1C',
              boxShadow: 'var(--shadow-sm)',
            }}>
              {actionMsg}
            </span>
          )}

          {policy.decision === 'AUTO' && !['RECOVERED', 'CLOSED', 'ACTION_SENT'].includes(c.status) && (
            <button className="btn btn-primary" onClick={handleRecover}>
              ⚡ RECOVER NOW (PAYMENT LINK)
            </button>
          )}

          {(c.status === 'QUEUED_FOR_REVIEW' || policy.decision === 'QUEUE_FOR_REVIEW') && (
            <>
              <button className="btn btn-success" onClick={handleApprove}>
                ✓ APPROVE RECOVERY
              </button>
              <button className="btn btn-danger" onClick={handleReject}>
                ✗ REJECT / SUPPRESS
              </button>
            </>
          )}
        </div>
      </div>

      {/* Primary Key Metric Cards */}
      <div className="summary-grid" style={{ marginBottom: 24 }}>
        <div className="stat-card" style={{ '--card-accent': 'var(--color-dark)' }}>
          <div className="stat-label">INCIDENT AMOUNT</div>
          <div className="stat-value">{formatRupees(c.amount)}</div>
          <div className="stat-subvalue">INR (INTEGER PAISE)</div>
        </div>

        <div className="stat-card" style={{ '--card-accent': policy.decision === 'AUTO' ? '#4CAF50' : '#FAB95B' }}>
          <div className="stat-label">POLICY VERDICT</div>
          <div style={{ marginTop: 4 }}>
            <span className={policyBadgeClass(policy.decision)}>
              {policy.decision || '—'}
            </span>
          </div>
          <div className="stat-subvalue" style={{ marginTop: 8 }}>ENGINE VER. {policy.policy_version || 'v1'}</div>
        </div>

        <div className="stat-card" style={{ '--card-accent': '#547792' }}>
          <div className="stat-label">LIFECYCLE STATUS</div>
          <div style={{ marginTop: 4 }}>
            <span className={statusBadgeClass(c.status)}>
              {c.status || '—'}
            </span>
          </div>
          <div className="stat-subvalue" style={{ marginTop: 8 }}>UPDATED {formatDate(c.updated_at || c.created_at)}</div>
        </div>

        <div className="stat-card" style={{ '--card-accent': 'var(--color-accent)' }}>
          <div className="stat-label">PRIORITY SCORE</div>
          <div className="stat-value">{c.priority_score?.toLocaleString() || '0'}</div>
          <div className="stat-subvalue">PROB: {((c.recovery_probability || 0) * 100).toFixed(0)}%</div>
        </div>
      </div>

      {/* Segmented Cockpit Tabs */}
      <div className="tab-list">
        {TABS.map(t => (
          <button
            key={t.key}
            className={`tab-btn ${activeTab === t.key ? 'active' : ''}`}
            onClick={() => setActiveTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Panels */}
      {activeTab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 20 }}>
          {/* Diagnosis Telemetry */}
          <div className="card">
            <div className="section-title">
              <span>🔬</span>
              <span>Root Cause Diagnosis</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <div className="stat-label" style={{ marginBottom: 4 }}>CLASSIFIED BUCKET</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '15px', fontWeight: '800', textTransform: 'uppercase', color: 'var(--color-dark)' }}>
                  {diag.bucket?.replace(/_/g, ' ') || '—'}
                </div>
              </div>

              <div>
                <div className="stat-label" style={{ marginBottom: 4 }}>DIAGNOSIS METHOD</div>
                <span className={`chip ${diag.method === 'gemini' ? 'chip-review' : 'chip-pending'}`}>
                  METHOD: {diag.method?.toUpperCase() || '—'}
                </span>
              </div>

              <div>
                <div className="stat-label" style={{ marginBottom: 6 }}>
                  CONFIDENCE METRIC: {(conf * 100).toFixed(0)}%
                </div>
                <div className="confidence-bar-track" style={{ height: 10 }}>
                  <div
                    className="confidence-bar-fill"
                    style={{
                      width: `${(conf * 100).toFixed(0)}%`,
                      '--fill-color': confidenceColor(conf),
                    }}
                  />
                </div>
              </div>

              {diag.explanation && (
                <div>
                  <div className="stat-label" style={{ marginBottom: 4 }}>EVIDENCE SUMMARY</div>
                  <div style={{
                    fontSize: '13px',
                    color: 'var(--color-text-primary)',
                    backgroundColor: 'var(--color-bg-elevated)',
                    padding: '8px 12px',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-sm)'
                  }}>
                    {diag.explanation}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Smart Dunning Engine Recommendation */}
          {detail.dunning_recommendation && (
            <div className="card" style={{ borderLeft: '6px solid var(--color-accent)' }}>
              <div className="section-title">
                <span>⏱</span>
                <span>Smart Dunning // Optimal Debit Window</span>
                <span className="chip chip-active" style={{ marginLeft: 'auto', fontSize: '10px' }}>
                  {detail.dunning_recommendation.tag}
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div style={{
                  backgroundColor: 'var(--color-bg-elevated)',
                  border: '2px solid var(--color-border)',
                  padding: '12px',
                  boxShadow: 'var(--shadow-sm)'
                }}>
                  <div className="stat-label" style={{ marginBottom: 4 }}>RECOMMENDED RETRY WINDOW</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', fontWeight: '800', color: 'var(--color-dark)' }}>
                    {detail.dunning_recommendation.window}
                  </div>
                  <div style={{ fontSize: '12px', color: '#1B5E20', fontWeight: '700', marginTop: 4 }}>
                    📈 {detail.dunning_recommendation.confidence_lift}
                  </div>
                </div>

                <div>
                  <div className="stat-label" style={{ marginBottom: 4 }}>EXECUTION PROTOCOL</div>
                  <div style={{ fontSize: '13px', color: 'var(--color-text-primary)' }}>
                    {detail.dunning_recommendation.protocol}
                  </div>
                </div>

                <div style={{
                  fontSize: '12px',
                  color: 'var(--color-text-muted)',
                  borderTop: '1px dashed var(--color-border)',
                  paddingTop: '8px'
                }}>
                  <strong>Banking Rationale (NPCI/RBI):</strong> {detail.dunning_recommendation.rationale}
                </div>
              </div>
            </div>
          )}

          {/* Policy Verification Checklist */}
          <div className="card">
            <PolicyChecklist policy={policy} />
          </div>

          {/* Event Ingestion Payload */}
          <div className="card">
            <div className="section-title">
              <span>📡</span>
              <span>Ingested Event Telemetry</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: '13px' }}>
              {[
                ['EVENT ID', event.event_id],
                ['REASON CODE', event.reason],
                ['GATEWAY MSG', event.gateway_message],
                ['ATTEMPT COUNT', event.attempt_count],
                ['CUSTOMER REF', c.customer_id],
                ['MERCHANT REF', c.merchant_id],
                ['TIMESTAMP', formatDate(event.occurred_at)],
              ].map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border)', paddingBottom: '6px' }}>
                  <span className="stat-label">{k}</span>
                  <span style={{
                    fontFamily: 'var(--font-mono)',
                    fontWeight: '600',
                    color: 'var(--color-dark)',
                    textAlign: 'right',
                    maxWidth: '60%',
                    wordBreak: 'break-all'
                  }}>
                    {v || '—'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Mathematical Scoring Ledger */}
          <div className="card">
            <div className="section-title">
              <span>📐</span>
              <span>Deterministic Scoring Formulation</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: '13px' }}>
              {[
                ['RECOVERY PROBABILITY', `${((c.recovery_probability || 0) * 100).toFixed(1)}%`],
                ['RECOVERABILITY CLASS', (c.recoverability || '—').toUpperCase()],
                ['CALCULATED PRIORITY', c.priority_score?.toLocaleString() || '0'],
              ].map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border)', paddingBottom: '6px' }}>
                  <span className="stat-label">{k}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '800', color: 'var(--color-dark)' }}>{v}</span>
                </div>
              ))}
            </div>
            <div style={{
              marginTop: 16,
              fontSize: '11px',
              color: 'var(--color-dark)',
              backgroundColor: 'var(--color-bg-elevated)',
              border: '2px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              padding: '10px 14px',
              fontFamily: 'var(--font-mono)',
              boxShadow: 'var(--shadow-sm)'
            }}>
              FORMULA: priority_score = amount_in_rupees × recovery_probability
            </div>
          </div>
        </div>
      )}

      {activeTab === 'audit' && (
        <div className="card">
          <div className="section-title">
            <span>📜</span>
            <span>Immutable Append-Only Audit Trail</span>
          </div>
          <AuditTimeline audit={audit} />
        </div>
      )}

      {activeTab === 'message' && (
        <div className="card">
          <div className="section-title">
            <span>💬</span>
            <span>Stored Customer Outreach</span>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginBottom: 20 }}>
            Exact WhatsApp communication synthesized at recovery execution. Stored immutably without re-calling the AI engine.
          </p>
          <MessagePreview caseId={caseId} />
        </div>
      )}
    </div>
  );
}
