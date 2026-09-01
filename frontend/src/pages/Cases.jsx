import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, formatRupees, formatDate, policyBadgeClass, statusBadgeClass, confidenceColor } from '../api';

const POLICY_FILTERS = [
  { label: 'All', value: undefined },
  { label: 'AUTO', value: 'AUTO' },
  { label: 'Review', value: 'QUEUE_FOR_REVIEW' },
  { label: 'Blocked', value: 'BLOCKED' },
];

export default function Cases() {
  const navigate = useNavigate();
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState(undefined);

  useEffect(() => {
    setLoading(true);
    api.getCases({ decision: filter, limit: 100 })
      .then(d => setCases(d.cases || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [filter]);

  if (loading) return <div className="loading"><div className="spinner" /> Loading cases...</div>;

  return (
    <div>
      <div className="page-header">
        <h2>Recovery Cases</h2>
        <p>Sorted by priority score (amount × recovery probability) — descending</p>
      </div>

      <div className="filter-row">
        {POLICY_FILTERS.map(f => (
          <button key={f.label} className={`filter-btn ${filter === f.value ? 'active' : ''}`}
            onClick={() => setFilter(f.value)}>
            {f.label}
          </button>
        ))}
        <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--text-muted)', alignSelf: 'center' }}>
          {cases.length} cases
        </span>
      </div>

      {cases.length === 0 ? (
        <div className="empty-state"><p>No cases found. Seed demo data from the Dashboard.</p></div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Case ID</th>
                <th>Amount</th>
                <th>Policy</th>
                <th>Status</th>
                <th>Root Cause</th>
                <th>Confidence</th>
                <th>Priority Score</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {cases.map(c => {
                const diag = c.diagnosis || {};
                const conf = diag.confidence || 0;
                return (
                  <tr key={c.case_id} onClick={() => navigate(`/cases/${c.case_id}`)}>
                    <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{c.case_id}</td>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{formatRupees(c.amount)}</td>
                    <td>
                      <span className={policyBadgeClass((c.policy || {}).decision)}>
                        {(c.policy || {}).decision || '—'}
                      </span>
                    </td>
                    <td>
                      <span className={statusBadgeClass(c.status)}>{c.status || '—'}</span>
                    </td>
                    <td style={{ fontSize: 12 }}>{diag.bucket?.replace(/_/g, ' ') || '—'}</td>
                    <td>
                      <div className="confidence-bar">
                        <div className="confidence-bar-track">
                          <div className="confidence-bar-fill"
                            style={{ width: `${(conf * 100).toFixed(0)}%`, '--fill-color': confidenceColor(conf) }} />
                        </div>
                        <span style={{ fontSize: 11, color: 'var(--text-muted)', width: 36 }}>
                          {(conf * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{c.priority_score?.toLocaleString() || '—'}</td>
                    <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{formatDate(c.created_at)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
