import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, formatRupees, formatDate, confidenceColor } from '../api';

export default function ReviewQueue() {
  const navigate = useNavigate();
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionMsgs, setActionMsgs] = useState({});

  const load = () => {
    setLoading(true);
    api.getCases({ decision: 'QUEUE_FOR_REVIEW', limit: 100 })
      .then(d => setCases(d.cases || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const setMsg = (caseId, msg) => setActionMsgs(p => ({ ...p, [caseId]: msg }));

  const handleApprove = async (caseId) => {
    setMsg(caseId, 'Approving...');
    try {
      await api.approveCase(caseId);
      setMsg(caseId, '✓ Approved');
      setTimeout(load, 1500);
    } catch (e) {
      setMsg(caseId, '✗ ' + e.message);
    }
  };

  const handleReject = async (caseId) => {
    setMsg(caseId, 'Rejecting...');
    try {
      await api.rejectCase(caseId, 'Rejected from review queue');
      setMsg(caseId, '✓ Rejected');
      setTimeout(load, 1500);
    } catch (e) {
      setMsg(caseId, '✗ ' + e.message);
    }
  };

  if (loading) return <div className="loading"><div className="spinner" /> Loading review queue...</div>;

  return (
    <div>
      <div className="page-header">
        <h2>Review Queue</h2>
        <p>{cases.length} case{cases.length !== 1 ? 's' : ''} waiting for human decision</p>
      </div>

      {cases.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <p style={{ fontSize: 32, marginBottom: 12 }}>✅</p>
            <p>No cases in review queue. All clear!</p>
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {cases.map(c => {
            const diag = c.diagnosis || {};
            const policy = c.policy || {};
            const conf = diag.confidence || 0;
            const msg = actionMsgs[c.case_id];

            return (
              <div key={c.case_id} className="card" style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 20, alignItems: 'center' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr auto auto', gap: 24, alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>Amount</div>
                    <div style={{ fontSize: 20, fontWeight: 700 }}>{formatRupees(c.amount)}</div>
                  </div>

                  <div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>Root Cause</div>
                    <div style={{ fontSize: 13, fontWeight: 500 }}>{diag.bucket?.replace(/_/g, ' ') || '—'}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>via {diag.method}</div>
                  </div>

                  <div style={{ minWidth: 120 }}>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>Confidence: {(conf * 100).toFixed(0)}%</div>
                    <div className="confidence-bar-track" style={{ height: 6, borderRadius: 3 }}>
                      <div className="confidence-bar-fill" style={{ width: `${(conf * 100).toFixed(0)}%`, '--fill-color': confidenceColor(conf), height: '100%' }} />
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>Why review?</div>
                    <div style={{ fontSize: 12, color: 'var(--accent-amber)', maxWidth: 300 }}>
                      {(policy.reasons || []).slice(0, 2).join(' · ')}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'flex-end' }}>
                  {msg ? (
                    <span style={{ fontSize: 12, color: msg.startsWith('✓') ? 'var(--accent-green)' : msg.startsWith('✗') ? 'var(--accent-red)' : 'var(--text-muted)' }}>
                      {msg}
                    </span>
                  ) : (
                    <>
                      <button className="btn btn-success" style={{ fontSize: 12, width: 120 }} onClick={() => handleApprove(c.case_id)}>
                        ✓ Approve
                      </button>
                      <button className="btn btn-danger" style={{ fontSize: 12, width: 120 }} onClick={() => handleReject(c.case_id)}>
                        ✗ Reject
                      </button>
                      <button className="btn btn-ghost" style={{ fontSize: 12, width: 120 }} onClick={() => navigate(`/cases/${c.case_id}`)}>
                        View Detail
                      </button>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
