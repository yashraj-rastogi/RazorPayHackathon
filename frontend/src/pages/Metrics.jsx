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

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" />
        <span>READING EVALUATION TELEMETRY...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <div className="page-header">
          <h2>Benchmarking & Evaluation Matrix</h2>
          <p>Reproducible test evaluation run from evaluation/evaluate.py</p>
        </div>
        <div className="card">
          <div className="empty-state">
            <p style={{ fontSize: '36px', marginBottom: '8px' }}>📉</p>
            <p style={{ fontFamily: 'var(--font-heading)', fontWeight: '700', fontSize: '16px' }}>
              NO EVALUATION RUN DETECTED
            </p>
            <p style={{ fontSize: '13px', marginTop: 8 }}>
              To compute metrics against ground-truth labels, run:
            </p>
            <pre style={{
              display: 'inline-block',
              marginTop: 12,
              padding: '10px 16px',
              backgroundColor: 'var(--color-bg-elevated)',
              border: '2px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              fontFamily: 'var(--font-mono)',
              fontSize: '12px',
              boxShadow: 'var(--shadow-sm)'
            }}>
              python evaluation/evaluate.py --dataset data/generated/v1.json --labels evaluation/labels.json --firestore
            </pre>
          </div>
        </div>
      </div>
    );
  }

  const m = metrics;
  const pct = (v) => v !== undefined ? `${(v * 100).toFixed(1)}%` : '—';
  const num = (v) => v?.toLocaleString() ?? '—';

  const rows = [
    ['BENCHMARK DATASET VER.', `v${m.dataset_version || '1'}`],
    ['PSEUDO-RANDOM SEED', `${m.seed ?? 42}`],
    ['RECORDS PROCESSED', num(m.records_processed)],
    ['AUTOMATED CASES (AUTO)', num(m.auto_count)],
    ['ESCALATED REVIEW CASES', num(m.review_count)],
    ['SAFETY-BLOCKED CASES', num(m.blocked_count)],
    ['RECOVERABLE UNIVERSE', num(m.recoverable_cases)],
    ['RECOVERY RATE (AUTO / RECOVERABLE)', pct(m.recovery_rate)],
    ['AUTOMATION EFFICIENCY (AUTO / TOTAL)', pct(m.automation_rate)],
    ['DIAGNOSTIC VERIFICATION ACCURACY', pct(m.diagnosis_accuracy)],
    ['TOTAL REVENUE AT RISK (PAISE / INR)', m.total_revenue_at_risk !== undefined ? `₹${((m.total_revenue_at_risk) / 100).toLocaleString('en-IN')}` : '—'],
    ['ESTIMATED RECOVERED REVENUE', m.recovered_revenue !== undefined ? `₹${((m.recovered_revenue) / 100).toLocaleString('en-IN')}` : '—'],
    ['GROUND-TRUTH LABELED INCIDENTS', num(m.labeled_cases)],
    ['ACCURATE GROUND-TRUTH MATCHES', num(m.correct_policy_labels)],
  ];

  return (
    <div>
      <div className="page-header">
        <h2>Benchmarking & Evaluation Matrix</h2>
        <p>Ground-truth telemetry · Run ID: {m.run_id || 'N/A'}</p>
      </div>

      {/* Primary KPI Scoreboard */}
      <div className="summary-grid" style={{ marginBottom: 24 }}>
        <div className="stat-card" style={{ '--card-accent': '#4CAF50' }}>
          <div className="stat-label">RECOVERY SUCCESS RATE</div>
          <div className="stat-value" style={{ color: '#1B5E20' }}>{pct(m.recovery_rate)}</div>
          <div className="stat-subvalue">AUTO / RECOVERABLE POOL</div>
        </div>

        <div className="stat-card" style={{ '--card-accent': 'var(--color-dark)' }}>
          <div className="stat-label">AUTOMATION EFFICIENCY</div>
          <div className="stat-value" style={{ color: 'var(--color-dark)' }}>{pct(m.automation_rate)}</div>
          <div className="stat-subvalue">TOTAL ZERO-TOUCH CASES</div>
        </div>

        <div className="stat-card" style={{ '--card-accent': 'var(--color-accent)' }}>
          <div className="stat-label">DIAGNOSTIC ACCURACY</div>
          <div className="stat-value" style={{ color: '#92400E' }}>{pct(m.diagnosis_accuracy)}</div>
          <div className="stat-subvalue">GROUND-TRUTH CONCORDANCE</div>
        </div>
      </div>

      {/* Detailed Ledger Matrix */}
      <div className="card">
        <div className="section-title">
          <span>📐</span>
          <span>Comprehensive Evaluation Ledger</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {rows.map(([k, v]) => (
            <div
              key={k}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontSize: '13px',
                borderBottom: '1px solid var(--color-border)',
                paddingBottom: '8px',
              }}
            >
              <span className="stat-label">{k}</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '800', color: 'var(--color-dark)' }}>
                {v}
              </span>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 20, fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--color-text-secondary)' }}>
          TIMESTAMP: {m.created_at || '—'} // DATA SOURCE: FIRESTORE EVALUATION_RUNS
        </div>
      </div>
    </div>
  );
}
