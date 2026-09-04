import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, formatRupees, confidenceColor } from '../api';

export default function ReviewQueue() {
  const navigate = useNavigate();
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionMsgs, setActionMsgs] = useState({});

  const [approvalModalCase, setApprovalModalCase] = useState(null);
  const [targetPhone, setTargetPhone] = useState('+917355788131');

  const load = () => {
    setLoading(true);
    api.getCases({ decision: 'QUEUE_FOR_REVIEW', limit: 100 })
      .then(d => setCases(d.cases || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const setMsg = (caseId, msg) => setActionMsgs(p => ({ ...p, [caseId]: msg }));

  const handleApprove = async (caseId, phoneOverride = null) => {
    setMsg(caseId, 'APPROVING...');
    try {
      await api.approveCase(caseId, phoneOverride ? { phone_override: phoneOverride } : {});
      setMsg(caseId, '✓ APPROVED & RECOVERY TRIGGERED');
      setTimeout(load, 1200);
    } catch (e) {
      setMsg(caseId, '✗ ' + e.message);
    }
  };

  const handleReject = async (caseId) => {
    setMsg(caseId, 'REJECTING...');
    try {
      await api.rejectCase(caseId, 'Rejected by operator from review queue');
      setMsg(caseId, '✓ CASE REJECTED & SUPPRESSED');
      setTimeout(load, 1200);
    } catch (e) {
      setMsg(caseId, '✗ ' + e.message);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" />
        <span>READING OPERATOR REVIEW QUEUE...</span>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h2>Operator Review Intercept Queue</h2>
        <p>Incidents exceeding risk thresholds, retry limits, or AI ambiguity bounds requiring human judgment</p>
      </div>

      {cases.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <p style={{ fontSize: '36px', marginBottom: '8px' }}>🛡</p>
            <p style={{ fontFamily: 'var(--font-heading)', fontWeight: '700', fontSize: '16px' }}>
              REVIEW QUEUE CLEAR
            </p>
            <p style={{ fontSize: '13px', marginTop: 4 }}>
              All automated policies operating within nominal confidence thresholds.
            </p>
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {cases.map(c => {
            const diag = c.diagnosis || {};
            const policy = c.policy || {};
            const conf = diag.confidence || 0;
            const msg = actionMsgs[c.case_id];

            return (
              <div
                key={c.case_id}
                className="card"
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr auto',
                  gap: 20,
                  alignItems: 'center',
                  borderLeft: '6px solid var(--color-accent)'
                }}
              >
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 20, alignItems: 'center' }}>
                  {/* Amount */}
                  <div>
                    <div className="stat-label">INCIDENT VALUE</div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '22px', fontWeight: '800', color: 'var(--color-dark)' }}>
                      {formatRupees(c.amount)}
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--color-text-secondary)', marginTop: 2 }}>
                      REF: {c.case_id}
                    </div>
                  </div>

                  {/* Diagnosis */}
                  <div>
                    <div className="stat-label">DIAGNOSIS VERDICT</div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', fontWeight: '700', textTransform: 'uppercase', color: 'var(--color-dark)' }}>
                      {diag.bucket?.replace(/_/g, ' ') || '—'}
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--color-text-muted)', marginTop: 2 }}>
                      METHOD: {diag.method?.toUpperCase()}
                    </div>
                  </div>

                  {/* Confidence Bar */}
                  <div style={{ minWidth: 140 }}>
                    <div className="stat-label" style={{ marginBottom: 4 }}>
                      CONFIDENCE: {(conf * 100).toFixed(0)}%
                    </div>
                    <div className="confidence-bar-track" style={{ height: 8 }}>
                      <div
                        className="confidence-bar-fill"
                        style={{
                          width: `${(conf * 100).toFixed(0)}%`,
                          '--fill-color': confidenceColor(conf),
                        }}
                      />
                    </div>
                  </div>

                  {/* Reason for Escalation */}
                  <div>
                    <div className="stat-label">ESCALATION TRIGGER</div>
                    <div style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '11px',
                      fontWeight: '600',
                      color: '#92400E',
                      backgroundColor: 'rgba(250, 185, 91, 0.25)',
                      padding: '4px 8px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid #D97706',
                      marginTop: 2
                    }}>
                      {(policy.reasons || []).slice(0, 1).join('') || 'Threshold exceeded'}
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'flex-end', minWidth: 150 }}>
                  {msg ? (
                    <span style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '11px',
                      fontWeight: '700',
                      padding: '6px 10px',
                      border: '2px solid var(--color-border)',
                      backgroundColor: msg.startsWith('✓') ? 'rgba(76, 175, 80, 0.15)' : 'rgba(229, 57, 53, 0.15)',
                      color: msg.startsWith('✓') ? '#1B5E20' : '#B71C1C',
                      textAlign: 'center'
                    }}>
                      {msg}
                    </span>
                  ) : (
                    <>
                      <button
                        className="btn btn-success"
                        style={{ fontSize: '11px', width: '100%' }}
                        onClick={() => {
                          setApprovalModalCase(c);
                          setTargetPhone('+917355788131');
                        }}
                      >
                        ✓ APPROVE RECOVERY
                      </button>
                      <button
                        className="btn btn-danger"
                        style={{ fontSize: '11px', width: '100%' }}
                        onClick={() => handleReject(c.case_id)}
                      >
                        ✗ SUPPRESS / BLOCK
                      </button>
                      <button
                        className="btn btn-ghost"
                        style={{ fontSize: '11px', width: '100%' }}
                        onClick={() => navigate(`/cases/${c.case_id}`)}
                      >
                        INSPECT TELEMETRY
                      </button>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* WhatsApp Outreach Dispatch Modal */}
      {approvalModalCase && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{ maxWidth: '520px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: '20px' }}>📱</span>
                <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '800' }}>DISPATCH RECOVERY TO WHATSAPP</h3>
              </div>
              <button
                className="btn btn-ghost"
                style={{ padding: '4px 10px', fontSize: '14px', fontWeight: '800' }}
                onClick={() => setApprovalModalCase(null)}
              >
                ✕
              </button>
            </div>

            <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginBottom: 16 }}>
              Approving this incident mints an official Razorpay Payment Link and dispatches a personalized recovery notification via Twilio WhatsApp API.
            </p>

            <div style={{ backgroundColor: 'var(--color-bg-surface)', border: '1px solid var(--color-border)', padding: 12, borderRadius: 'var(--radius-sm)', marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontSize: '12px', fontWeight: '700', color: 'var(--color-text-secondary)' }}>INCIDENT REF</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', fontWeight: '700' }}>{approvalModalCase.case_id}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '12px', fontWeight: '700', color: 'var(--color-text-secondary)' }}>RECOVERY VALUE</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', fontWeight: '800', color: 'var(--color-dark)' }}>{formatRupees(approvalModalCase.amount)}</span>
              </div>
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Recipient WhatsApp Number (E.164 Format)
              </label>
              <input
                type="text"
                value={targetPhone}
                onChange={e => setTargetPhone(e.target.value)}
                placeholder="+919876543210"
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '14px',
                  fontWeight: '700',
                  border: '2px solid var(--color-border)',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'var(--color-bg-base)',
                  color: 'var(--color-dark)',
                  outline: 'none',
                  boxSizing: 'border-box',
                }}
              />
            </div>

            <div style={{
              backgroundColor: '#FFFDF5',
              border: '1px solid #D97706',
              borderRadius: 'var(--radius-sm)',
              padding: 12,
              fontSize: '12px',
              lineHeight: '1.5',
              color: '#92400E',
              marginBottom: 20,
            }}>
              <strong>💡 Testing with Your Personal WhatsApp?</strong><br />
              If your phone has not joined this Twilio Sandbox before, open WhatsApp and send <code>join breakfast-mountain</code> to <code>+1 415 523 8886</code> first.
            </div>

            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
              <button
                className="btn btn-ghost"
                onClick={() => setApprovalModalCase(null)}
              >
                CANCEL
              </button>
              <button
                className="btn btn-success"
                style={{ fontWeight: '800' }}
                onClick={() => {
                  const cId = approvalModalCase.case_id;
                  setApprovalModalCase(null);
                  handleApprove(cId, targetPhone);
                }}
              >
                🚀 APPROVE & DISPATCH TO WHATSAPP
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
