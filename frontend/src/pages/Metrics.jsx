import { useEffect, useState } from 'react';
import { api } from '../api';

export default function Metrics() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.getMetrics()
      .then(setMetrics)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading"><div className="spinner" /> Loading metrics...</div>;

  if (error) return (
    <div>
      <div className="page-header">
        <h2>Evaluation Metrics</h2>
        <p>Powered by evaluation/evaluate.py — run separately from live dashboard</p>
      </div>
      <div className="card">
        <div className="empty-state">
          <p style={{ fontSize: 32, marginBottom: 12 }}>📊</p>
          <p>No evaluation run found.</p>
          <p style={{ marginTop: 8, fontSize: 12 }}>Run: <code>python evaluation/evaluate.py --firestore</code></p>
        </div>
      </div>
    </div>
  );

  const m = metrics;
  const pct = (v) => v !== undefined ? `${(v * 100).toFixed(1)}%` : '—';
  const num = (v) => v?.toLocaleString() ?? '—';

  const rows = [
    ['Records Processed', num(m.records_processed)],
    ['AUTO Cases', num(m.auto_count)],
    ['Review Cases', num(m.review_count)],
    ['Blocked Cases', num(m.blocked_count)],
    ['Errors', num(m.errors)],
    ['Recoverable Cases', num(m.recoverable_cases)],
    ['Recovery Rate (AUTO/Recoverable)', pct(m.recovery_rate)],
    ['Automation Rate (AUTO/Total)', pct(m.automation_rate)],
    ['Diagnosis Accuracy', pct(m.diagnosis_accuracy)],
    ['Revenue at Risk', m.total_revenue_at_risk !== undefined ? `₹${(m.total_revenue_at_risk / 100).toLocaleString('en-IN')}` : '—'],
    ['Recovered Revenue (est.)', m.recovered_revenue !== undefined ? `₹${(m.recovered_revenue / 100).toLocaleString('en-IN')}` : '—'],
    ['Labeled Cases', num(m.labeled_cases)],
    ['Correct Policy Labels', num(m.correct_policy_labels)],
  ];

  return (
    <div>
      <div className="page-header">
        <h2>Evaluation Metrics</h2>
        <p>Dataset v{m.dataset_version} · Seed {m.seed} · Run {m.run_id}</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 24 }}>
        {[
          { label: 'Recovery Rate', value: pct(m.recovery_rate), color: 'var(--accent-green)' },
          { label: 'Automation Rate', value: pct(m.automation_rate), color: 'var(--accent-blue)' },
          { label: 'Diagnosis Accuracy', value: pct(m.diagnosis_accuracy), color: 'var(--accent-purple)' },
        ].map(item => (
          <div key={item.label} className="summary-card" style={{ '--card-accent': item.color }}>
            <div className="label">{item.label}</div>
            <div className="value" style={{ color: item.color }}>{item.value}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 20 }}>Full Metrics</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {rows.map(([k, v]) => (
            <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, borderBottom: '1px solid var(--border)', paddingBottom: 10 }}>
              <span style={{ color: 'var(--text-secondary)' }}>{k}</span>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'monospace' }}>{v}</span>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 16, fontSize: 11, color: 'var(--text-muted)' }}>
          Run at: {m.created_at} · These are real metrics, not example values.
        </div>
      </div>
    </div>
  );
}
