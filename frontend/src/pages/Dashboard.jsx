import { useEffect, useState } from 'react';
import { api, formatRupees } from '../api';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis } from 'recharts';

const BUCKET_COLORS = {
  temporary_failure: '#1A3263',            // Blueprint Navy
  insufficient_funds: '#FAB95B',           // Industrial Amber
  payment_credential_expired: '#547792',   // Slate Steel
  mandate_inactive: '#E53935',             // Alert Red
  otp_or_authentication_issue: '#8B5CF6',  // Tactical Purple
  unknown: '#94A3B8',                      // Muted Slate
};

const BUCKET_LABELS = {
  temporary_failure: 'Temp Failure',
  insufficient_funds: 'Insuff. Funds',
  payment_credential_expired: 'Expired Creds',
  mandate_inactive: 'Mandate Inactive',
  otp_or_authentication_issue: 'OTP/Auth Issue',
  unknown: 'Unknown / AI',
};

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [seedMsg, setSeedMsg] = useState('');

  const load = () => {
    setLoading(true);
    api.getDashboard()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleSeed = async () => {
    setSeeding(true);
    setSeedMsg('');
    try {
      const r = await api.seedDataset({ count: 50, seed: 42 });
      setSeedMsg(`✓ SEEDED ${r.records_created} CASES (${r.duplicates_blocked} DUPLICATES FILTERED)`);
      load();
    } catch (e) {
      setSeedMsg('✗ ' + e.message);
    } finally {
      setSeeding(false);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" />
        <span>READING COCKPIT TELEMETRY...</span>
      </div>
    );
  }

  const rootCauseData = Object.entries(data?.root_causes || {}).map(([k, v]) => ({
    name: BUCKET_LABELS[k] || k,
    value: v,
    key: k,
  }));

  const policyData = [
    { name: 'AUTO', value: data?.cases?.auto || 0, color: '#4CAF50' },
    { name: 'REVIEW', value: data?.cases?.review || 0, color: '#FAB95B' },
    { name: 'BLOCKED', value: data?.cases?.blocked || 0, color: '#E53935' },
  ];

  const recoveryPct = data?.recovery_rate ? `${(data.recovery_rate * 100).toFixed(1)}%` : '0.0%';

  return (
    <div>
      {/* Top Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h2>Telemetry & Recovery Cockpit</h2>
          <p>Live Firestore event stream · Deterministic policy verification</p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          {seedMsg && (
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              fontWeight: '700',
              padding: '6px 12px',
              border: '2px solid var(--color-border)',
              backgroundColor: seedMsg.startsWith('✓') ? 'rgba(76, 175, 80, 0.15)' : 'rgba(229, 57, 53, 0.15)',
              color: seedMsg.startsWith('✓') ? '#1B5E20' : '#B71C1C',
              boxShadow: 'var(--shadow-sm)',
            }}>
              {seedMsg}
            </span>
          )}
          <button className="btn btn-ghost" onClick={load}>↻ REFRESH</button>
          <button className="btn btn-primary" onClick={handleSeed} disabled={seeding}>
            {seeding ? 'SEEDING DATABASE...' : '⚡ SEED DEMO TELEMETRY'}
          </button>
        </div>
      </div>

      {/* Primary KPI Operator Cards */}
      <div className="summary-grid">
        <div className="stat-card" style={{ '--card-accent': '#E53935' }}>
          <div className="stat-label">REVENUE AT RISK</div>
          <div className="stat-value" style={{ color: 'var(--color-danger)' }}>{formatRupees(data?.revenue_at_risk)}</div>
          <div className="stat-subvalue">{data?.total_cases || 0} TOTAL CASES INGESTED</div>
        </div>

        <div className="stat-card" style={{ '--card-accent': '#4CAF50' }}>
          <div className="stat-label">REVENUE RECOVERED</div>
          <div className="stat-value" style={{ color: '#1B5E20' }}>{formatRupees(data?.revenue_recovered)}</div>
          <div className="stat-subvalue">RECOVERY RATE: {recoveryPct}</div>
        </div>

        <div className="stat-card" style={{ '--card-accent': '#4CAF50' }}>
          <div className="stat-label">AUTO ACTIONS</div>
          <div className="stat-value" style={{ color: '#1B5E20' }}>{data?.cases?.auto || 0}</div>
          <div className="stat-subvalue">FULL AUTOMATION PIPELINE</div>
        </div>

        <div className="stat-card" style={{ '--card-accent': '#FAB95B' }}>
          <div className="stat-label">REVIEW QUEUE</div>
          <div className="stat-value" style={{ color: '#92400E' }}>{data?.cases?.review || 0}</div>
          <div className="stat-subvalue">HUMAN OPERATOR APPROVAL REQ.</div>
        </div>

        <div className="stat-card" style={{ '--card-accent': '#E53935' }}>
          <div className="stat-label">BLOCKED CASES</div>
          <div className="stat-value" style={{ color: 'var(--color-danger)' }}>{data?.cases?.blocked || 0}</div>
          <div className="stat-subvalue">OPT-OUT / CANCELLED / ALREADY PAID</div>
        </div>
      </div>

      {/* Blueprint Analytics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20, marginBottom: 24 }}>
        {/* Root Causes Chart */}
        <div className="card">
          <div className="section-title">
            <span>📊</span>
            <span>Root Cause Breakdown</span>
          </div>
          {rootCauseData.length > 0 ? (
            <div>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={rootCauseData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={3}
                    dataKey="value"
                    stroke="#0F172A"
                    strokeWidth={2}
                  >
                    {rootCauseData.map((entry) => (
                      <Cell key={entry.key} fill={BUCKET_COLORS[entry.key] || '#94A3B8'} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'var(--color-bg-surface)',
                      border: 'var(--border-thick)',
                      borderRadius: 'var(--radius-sm)',
                      boxShadow: 'var(--shadow-md)',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '12px',
                      color: 'var(--color-dark)',
                      fontWeight: '700',
                    }}
                    formatter={(val, name) => [`${val} CASES`, name]}
                  />
                </PieChart>
              </ResponsiveContainer>

              {/* Legend Matrix */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 8, marginTop: 12 }}>
                {rootCauseData.map(e => (
                  <div key={e.key} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '4px 8px',
                    border: '1px solid var(--color-border)',
                    backgroundColor: 'var(--color-bg-elevated)',
                    borderRadius: 'var(--radius-sm)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '11px',
                  }}>
                    <div style={{ width: 10, height: 10, backgroundColor: BUCKET_COLORS[e.key] || '#94A3B8', border: '1px solid var(--color-dark)' }} />
                    <span style={{ fontWeight: '600', color: 'var(--color-dark)' }}>{e.name}: {e.value}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <p>NO TELEMETRY DATA INGESTED. CLICK "SEED DEMO TELEMETRY".</p>
            </div>
          )}
        </div>

        {/* Policy Distribution Bar Chart */}
        <div className="card">
          <div className="section-title">
            <span>⚖️</span>
            <span>Policy Execution Verdicts</span>
          </div>
          {policyData.some(d => d.value > 0) ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={policyData} barSize={44} margin={{ top: 20, right: 10, left: -20, bottom: 0 }}>
                <XAxis
                  dataKey="name"
                  tick={{ fill: 'var(--color-dark)', fontFamily: 'var(--font-heading)', fontWeight: '700', fontSize: 12 }}
                  axisLine={{ stroke: 'var(--color-border)', strokeWidth: 2 }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: 'var(--color-text-secondary)', fontFamily: 'var(--font-mono)', fontSize: 11 }}
                  axisLine={{ stroke: 'var(--color-border)', strokeWidth: 2 }}
                  tickLine={false}
                />
                <Tooltip
                  cursor={{ fill: 'rgba(26, 50, 99, 0.05)' }}
                  contentStyle={{
                    backgroundColor: 'var(--color-bg-surface)',
                    border: 'var(--border-thick)',
                    borderRadius: 'var(--radius-sm)',
                    boxShadow: 'var(--shadow-md)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '12px',
                    color: 'var(--color-dark)',
                    fontWeight: '700',
                  }}
                  formatter={(val) => [`${val} CASES`, 'VOLUME']}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]} stroke="#0F172A" strokeWidth={2}>
                  {policyData.map((d) => (
                    <Cell key={d.name} fill={d.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state">
              <p>NO POLICY VERDICTS AVAILABLE.</p>
            </div>
          )}
        </div>
      </div>

      {/* Failure Injection Hardware Panel */}
      <div className="card">
        <div className="section-title">
          <span>🛠</span>
          <span>Simulation & Failure Injection Switchboard</span>
        </div>
        <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: 14 }}>
          Trigger simulated edge cases into the live ingestion pipeline to verify deterministic recovery physics:
        </p>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {[
            { type: 'duplicate_event', label: 'REPEAT IDENTICAL EVENT (IDEMPOTENCY)' },
            { type: 'already_successful', label: 'ALREADY CHARGED (SAFETY BLOCK)' },
            { type: 'retry_limit', label: 'RETRY LIMIT HIT (REVIEW ESCALATION)' },
            { type: 'gemini_timeout', label: 'AI TIMEOUT (FALLBACK RESILIENCE)' },
          ].map(sim => (
            <button
              key={sim.type}
              className="btn btn-ghost"
              style={{ fontSize: '11px', fontFamily: 'var(--font-mono)' }}
              onClick={() => api.simulateFailure(sim.type).then(() => load()).catch(e => alert(e.message))}
            >
              ▶ {sim.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
