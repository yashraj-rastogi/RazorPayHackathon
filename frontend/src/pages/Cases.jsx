import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, formatRupees, formatDate, policyBadgeClass, statusBadgeClass, confidenceColor } from '../api';

const POLICY_FILTERS = [
  { label: 'ALL CASES', value: undefined },
  { label: 'AUTO RECOVERY', value: 'AUTO' },
  { label: 'REQUIRES REVIEW', value: 'QUEUE_FOR_REVIEW' },
  { label: 'BLOCKED', value: 'BLOCKED' },
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

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" />
        <span>PAGING INCIDENT LEDGER...</span>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h2>Incident Recovery Ledger</h2>
        <p>Ranked deterministically by Priority Score (Amount × Recovery Probability)</p>
      </div>

      {/* Tactical Filter Row */}
      <div className="filter-row">
        {POLICY_FILTERS.map(f => (
          <button
            key={f.label}
            className={`filter-btn ${filter === f.value ? 'active' : ''}`}
            onClick={() => setFilter(f.value)}
          >
            {f.label}
          </button>
        ))}
        <span style={{
          marginLeft: 'auto',
          fontFamily: 'var(--font-mono)',
          fontSize: '12px',
          fontWeight: '700',
          color: 'var(--color-text-secondary)',
          alignSelf: 'center',
          border: '1px solid var(--color-border)',
          padding: '4px 10px',
          backgroundColor: 'var(--color-bg-surface)',
          boxShadow: 'var(--shadow-sm)'
        }}>
          {cases.length} INCIDENTS LOGGED
        </span>
      </div>

      {cases.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <p style={{ fontFamily: 'var(--font-heading)', fontWeight: '700' }}>NO INCIDENTS MATCH CRITERIA</p>
            <p style={{ fontSize: '13px', marginTop: 6 }}>Trigger telemetry from the Cockpit or adjust filters.</p>
          </div>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>CASE ID</th>
                <th>AMOUNT</th>
                <th>POLICY</th>
                <th>STATUS</th>
                <th>ROOT CAUSE</th>
                <th>AI CONFIDENCE</th>
                <th>PRIORITY SCORE</th>
                <th>TIMESTAMP</th>
              </tr>
            </thead>
            <tbody>
              {cases.map(c => {
                const diag = c.diagnosis || {};
                const conf = diag.confidence || 0;
                return (
                  <tr key={c.case_id} onClick={() => navigate(`/cases/${c.case_id}`)}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', fontWeight: '700', color: 'var(--color-dark)' }}>
                      {c.case_id}
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: '800', color: 'var(--color-dark)', fontSize: '14px' }}>
                      {formatRupees(c.amount)}
                    </td>
                    <td>
                      <span className={policyBadgeClass((c.policy || {}).decision)}>
                        {(c.policy || {}).decision || '—'}
                      </span>
                    </td>
                    <td>
                      <span className={statusBadgeClass(c.status)}>
                        {c.status || '—'}
                      </span>
                    </td>
                    <td style={{ fontSize: '12px', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: '600' }}>
                      {diag.bucket?.replace(/_/g, ' ') || '—'}
                    </td>
                    <td style={{ minWidth: '130px' }}>
                      <div className="confidence-bar">
                        <div className="confidence-bar-track">
                          <div
                            className="confidence-bar-fill"
                            style={{
                              width: `${(conf * 100).toFixed(0)}%`,
                              '--fill-color': confidenceColor(conf),
                            }}
                          />
                        </div>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', fontWeight: '700', minWidth: '32px' }}>
                          {(conf * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: '700', fontSize: '13px' }}>
                      {c.priority_score?.toLocaleString() || '0'}
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                      {formatDate(c.created_at)}
                    </td>
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
