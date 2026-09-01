import { useEffect, useState } from 'react';
import { api, formatRupees } from '../api';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis } from 'recharts';

const BUCKET_COLORS = {
  temporary_failure: '#3b82f6',
  insufficient_funds: '#f59e0b',
  payment_credential_expired: '#8b5cf6',
  mandate_inactive: '#ef4444',
  otp_or_authentication_issue: '#f97316',
  unknown: '#64748b',
};

const BUCKET_LABELS = {
  temporary_failure: 'Temp Failure',
  insufficient_funds: 'Insuff. Funds',
  payment_credential_expired: 'Expired Creds',
  mandate_inactive: 'Mandate Inactive',
  otp_or_authentication_issue: 'OTP/Auth Issue',
  unknown: 'Unknown',
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
      setSeedMsg(`✓ Seeded ${r.records_created} cases (${r.duplicates_blocked} duplicates blocked)`);
      load();
    } catch (e) {
      setSeedMsg('✗ ' + e.message);
    } finally {
      setSeeding(false);
    }
  };

  if (loading) return <div className="loading"><div className="spinner" /> Loading dashboard...</div>;

  const rootCauseData = Object.entries(data?.root_causes || {}).map(([k, v]) => ({
    name: BUCKET_LABELS[k] || k, value: v, key: k,
  }));

  const policyData = [
    { name: 'AUTO', value: data?.cases?.auto || 0, color: '#10b981' },
    { name: 'Review', value: data?.cases?.review || 0, color: '#f59e0b' },
    { name: 'Blocked', value: data?.cases?.blocked || 0, color: '#ef4444' },
  ];

  const recoveryPct = data?.recovery_rate ? `${(data.recovery_rate * 100).toFixed(1)}%` : '0%';

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2>Revenue Recovery Dashboard</h2>
          <p>Live data from Firestore — not cached from evaluation run</p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {seedMsg && <span style={{ fontSize: 12, color: seedMsg.startsWith('✓') ? 'var(--accent-green)' : 'var(--accent-red)' }}>{seedMsg}</span>}
          <button className="btn btn-ghost" onClick={load}>↻ Refresh</button>
          <button className="btn btn-primary" onClick={handleSeed} disabled={seeding}>
            {seeding ? 'Seeding...' : '+ Seed Demo Data'}
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="summary-grid">
        <div className="summary-card" style={{ '--card-accent': '#ef4444' }}>
          <div className="label">Revenue at Risk</div>
          <div className="value">{formatRupees(data?.revenue_at_risk)}</div>
          <div className="subvalue">{data?.total_cases || 0} total cases</div>
          <span className="icon" style={{ fontSize: 24 }}>⚠️</span>
        </div>

        <div className="summary-card" style={{ '--card-accent': '#10b981' }}>
          <div className="label">Revenue Recovered</div>
          <div className="value">{formatRupees(data?.revenue_recovered)}</div>
          <div className="subvalue">Recovery rate: {recoveryPct}</div>
          <span className="icon" style={{ fontSize: 24 }}>✅</span>
        </div>

        <div className="summary-card" style={{ '--card-accent': '#10b981' }}>
          <div className="label">AUTO Cases</div>
          <div className="value" style={{ color: 'var(--accent-green)' }}>{data?.cases?.auto || 0}</div>
          <div className="subvalue">Automated recovery</div>
          <span className="icon" style={{ fontSize: 24 }}>🤖</span>
        </div>

        <div className="summary-card" style={{ '--card-accent': '#f59e0b' }}>
          <div className="label">In Review Queue</div>
          <div className="value" style={{ color: 'var(--accent-amber)' }}>{data?.cases?.review || 0}</div>
          <div className="subvalue">Needs human decision</div>
          <span className="icon" style={{ fontSize: 24 }}>👁</span>
        </div>

        <div className="summary-card" style={{ '--card-accent': '#ef4444' }}>
          <div className="label">Blocked</div>
          <div className="value" style={{ color: 'var(--accent-red)' }}>{data?.cases?.blocked || 0}</div>
          <div className="subvalue">Opted-out / succeeded</div>
          <span className="icon" style={{ fontSize: 24 }}>🚫</span>
        </div>
      </div>

      {/* Charts row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
        {/* Root cause chart */}
        <div className="card">
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 20, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Root Causes</h3>
          {rootCauseData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={rootCauseData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {rootCauseData.map((entry) => (
                    <Cell key={entry.key} fill={BUCKET_COLORS[entry.key] || '#64748b'} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)' }}
                  formatter={(val, name) => [`${val} cases`, name]}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : <div className="empty-state"><p>No case data yet. Click "Seed Demo Data".</p></div>}

          {/* Legend */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
            {rootCauseData.map(e => (
              <div key={e.key} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11 }}>
                <div style={{ width: 8, height: 8, borderRadius: 2, background: BUCKET_COLORS[e.key] || '#64748b' }} />
                <span style={{ color: 'var(--text-secondary)' }}>{e.name}: {e.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Policy distribution chart */}
        <div className="card">
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 20, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Policy Decisions</h3>
          {policyData.some(d => d.value > 0) ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={policyData} barSize={40}>
                <XAxis dataKey="name" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)' }} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {policyData.map((d) => (
                    <Cell key={d.name} fill={d.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : <div className="empty-state"><p>No case data yet.</p></div>}
        </div>
      </div>

      {/* Simulate failures */}
      <div className="card">
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Demo Scenarios</h3>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {['duplicate_event', 'already_successful', 'retry_limit', 'gemini_timeout'].map(type => (
            <button key={type} className="btn btn-ghost" style={{ fontSize: 12 }}
              onClick={() => api.simulateFailure(type).then(() => load()).catch(e => alert(e.message))}>
              ▶ {type.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
