import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api, formatRupees, formatDate, policyBadgeClass, statusBadgeClass, confidenceColor } from '../api';

function PolicyChecklist({ policy, diagnosis }) {
  if (!policy) return null;
  const reasons = policy.reasons || [];
  const isAuto = policy.decision === 'AUTO';

  return (
    <div>
      <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>
        {isAuto ? 'Why we acted automatically' : policy.decision === 'BLOCKED' ? 'Why we blocked' : 'Why this needs review'}
      </h3>
      <div className="checklist">
        {reasons.map((r, i) => (
          <div key={i} className={`checklist-item ${isAuto ? 'pass' : policy.decision === 'BLOCKED' ? 'fail' : 'neutral'}`}>
            <span>{isAuto ? '✓' : policy.decision === 'BLOCKED' ? '✗' : '⚠'}</span>
            <span>{r}</span>
          </div>
        ))}
        {policy.block_reason && (
          <div className="checklist-item fail">
            <span>✗</span>
            <span>Block reason: {policy.block_reason}</span>
          </div>
        )}
      </div>
    </div>
  );
}

function AuditTimeline({ audit }) {
  const items = audit?.events || [];
  if (!items.length) return <div className="empty-state"><p>No audit entries yet.</p></div>;

  const actorClass = (actor) => ({
    system: 'timeline-dot-system',
    human: 'timeline-dot-human',
    webhook: 'timeline-dot-webhook',
  }[actor] || 'timeline-dot-system');

  const actorIcon = (actor) => ({
    system: '⚙', human: '👤', webhook: '🔗',
  }[actor] || '⚙');

  return (
    <div className="timeline">
      {items.map((item, i) => (
        <div key={i} className="timeline-item">
          <div className={`timeline-dot ${actorClass(item.actor)}`}>{actorIcon(item.actor)}</div>
          <div className="timeline-content">
            <div className="timeline-action">{item.action}</div>
            <div className="timeline-meta">
              {item.stage} · {item.actor} · {formatDate(item.timestamp)}
            </div>
            {item.details && Object.keys(item.details).length > 0 && (
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4, fontFamily: 'monospace' }}>
                {JSON.stringify(item.details, null, 2).slice(0, 200)}
              </div>
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

  if (loading) return <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>Loading message...</div>;
  if (!msg) return <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>No message generated yet. Recover the case to generate one.</div>;

  return (
    <div>
      <div className="message-bubble">
        {msg.message}
      </div>
      <div className="message-meta">
        <span>🌐 {msg.language}</span>
        <span>🎨 {msg.tone}</span>
        <span>📋 {msg.prompt_version}</span>
        <span>📤 {msg.sent ? `Sent ${formatDate(msg.sent_at)}` : 'Not yet sent'}</span>
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
    Promise.all([
      api.getCase(caseId),
      api.getCaseAudit(caseId),
    ]).then(([d, a]) => {
      setDetail(d);
      setAudit(a);
    }).catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [caseId]);

  const handleRecover = async () => {
    setActionMsg('Creating payment link...');
    try {
      const r = await api.recoverCase(caseId);
      setActionMsg(`✓ Payment link created: ${r.recovery_url || r.provider_reference}`);
      load();
    } catch (e) {
      setActionMsg('✗ ' + e.message);
    }
  };

  const handleApprove = async () => {
    setActionMsg('Approving...');
    try {
      const r = await api.approveCase(caseId);
      setActionMsg(`✓ Approved and recovering`);
      load();
    } catch (e) {
      setActionMsg('✗ ' + e.message);
    }
  };

  const handleReject = async () => {
    setActionMsg('Rejecting...');
    try {
      await api.rejectCase(caseId, 'Manually rejected from dashboard');
      setActionMsg('✓ Case rejected');
      load();
    } catch (e) {
      setActionMsg('✗ ' + e.message);
    }
  };

  if (loading) return <div className="loading"><div className="spinner" /> Loading case...</div>;
  if (!detail) return <div className="empty-state"><p>Case not found.</p></div>;

  const c = detail.case || {};
  const event = detail.event || {};
  const diag = c.diagnosis || {};
  const policy = c.policy || {};
  const conf = diag.confidence || 0;

  const TABS = ['overview', 'audit', 'message'];

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <button className="btn btn-ghost" onClick={() => navigate('/cases')}>← Back</button>
        <div>
          <h2 style={{ fontSize: 20, fontWeight: 700 }}>Case Detail</h2>
          <code style={{ fontSize: 12, color: 'var(--text-muted)' }}>{c.case_id}</code>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}>
          {actionMsg && (
            <span style={{ fontSize: 12, color: actionMsg.startsWith('✓') ? 'var(--accent-green)' : 'var(--accent-red)' }}>
              {actionMsg}
            </span>
          )}
          {policy.decision === 'AUTO' && !['RECOVERED', 'CLOSED', 'ACTION_SENT'].includes(c.status) && (
            <button className="btn btn-success" onClick={handleRecover}>⚡ Recover Now</button>
          )}
          {(c.status === 'QUEUED_FOR_REVIEW' || policy.decision === 'QUEUE_FOR_REVIEW') && (
            <>
              <button className="btn btn-success" onClick={handleApprove}>✓ Approve</button>
              <button className="btn btn-danger" onClick={handleReject}>✗ Reject</button>
            </>
          )}
        </div>
      </div>

      {/* Key facts row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        {[
          { label: 'Amount', value: formatRupees(c.amount), accent: '' },
          { label: 'Policy', value: <span className={policyBadgeClass(policy.decision)}>{policy.decision || '—'}</span> },
          { label: 'Status', value: <span className={statusBadgeClass(c.status)}>{c.status || '—'}</span> },
          { label: 'Priority Score', value: c.priority_score?.toLocaleString() || '—' },
        ].map(item => (
          <div key={item.label} className="card card-sm">
            <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>{item.label}</div>
            <div style={{ fontSize: 18, fontWeight: 700 }}>{item.value}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20 }}>
        {TABS.map(t => (
          <button key={t} className={`filter-btn ${activeTab === t ? 'active' : ''}`}
            onClick={() => setActiveTab(t)} style={{ textTransform: 'capitalize' }}>
            {t}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          {/* Diagnosis */}
          <div className="card">
            <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 16 }}>Diagnosis</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>Root Cause</div>
                <div style={{ fontWeight: 600 }}>{diag.bucket?.replace(/_/g, ' ') || '—'}</div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>Method</div>
                <span className={`badge ${diag.method === 'gemini' ? 'badge-review' : 'badge-pending'}`}>{diag.method || '—'}</span>
              </div>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>Confidence: {(conf * 100).toFixed(0)}%</div>
                <div className="confidence-bar-track" style={{ height: 8, borderRadius: 4 }}>
                  <div className="confidence-bar-fill" style={{ width: `${(conf * 100).toFixed(0)}%`, '--fill-color': confidenceColor(conf), height: '100%' }} />
                </div>
              </div>
              {diag.explanation && (
                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>Explanation</div>
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{diag.explanation}</div>
                </div>
              )}
            </div>
          </div>

          {/* Policy Checklist */}
          <div className="card">
            <PolicyChecklist policy={policy} diagnosis={diag} />
          </div>

          {/* Event details */}
          <div className="card">
            <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 16 }}>Event Details</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: 13 }}>
              {[
                ['Event ID', event.event_id],
                ['Reason Code', event.reason],
                ['Gateway Message', event.gateway_message],
                ['Attempt Count', event.attempt_count],
                ['Customer', c.customer_id],
                ['Merchant', c.merchant_id],
                ['Occurred At', formatDate(event.occurred_at)],
              ].map(([k, v]) => (
                <div key={k} style={{ display: 'flex', gap: 12 }}>
                  <span style={{ color: 'var(--text-muted)', width: 120, flexShrink: 0 }}>{k}</span>
                  <span style={{ color: 'var(--text-secondary)', fontFamily: k.includes('ID') ? 'monospace' : 'inherit', fontSize: k.includes('ID') ? 11 : 13 }}>{v || '—'}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Recovery scoring */}
          <div className="card">
            <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 16 }}>Recovery Scoring</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: 13 }}>
              {[
                ['Recovery Probability', `${((c.recovery_probability || 0) * 100).toFixed(1)}%`],
                ['Recoverability', c.recoverability || '—'],
                ['Priority Score', c.priority_score?.toLocaleString() || '—'],
              ].map(([k, v]) => (
                <div key={k} style={{ display: 'flex', gap: 12 }}>
                  <span style={{ color: 'var(--text-muted)', width: 160, flexShrink: 0 }}>{k}</span>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{v}</span>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16, fontSize: 11, color: 'var(--text-muted)', background: 'var(--bg-secondary)', borderRadius: 6, padding: '8px 12px', fontFamily: 'monospace' }}>
              priority_score = amount_rupees × recovery_probability
            </div>
          </div>
        </div>
      )}

      {activeTab === 'audit' && (
        <div className="card">
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 20 }}>Audit Trail</h3>
          <AuditTimeline audit={audit} />
        </div>
      )}

      {activeTab === 'message' && (
        <div className="card">
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 20 }}>Customer Message Preview</h3>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16 }}>
            This message was generated by Gemini and stored at the time of recovery. Not re-generated on view.
          </p>
          <MessagePreview caseId={caseId} />
        </div>
      )}
    </div>
  );
}
