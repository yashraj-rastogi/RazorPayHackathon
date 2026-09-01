import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { api, formatRupees } from '../api';

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/cases', label: 'All Cases', icon: '📋' },
  { path: '/review', label: 'Review Queue', icon: '👁', badge: true },
  { path: '/metrics', label: 'Metrics', icon: '📈' },
];

export function Layout({ children }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [reviewCount, setReviewCount] = useState(0);

  useEffect(() => {
    api.getCases({ decision: 'QUEUE_FOR_REVIEW', limit: 100 })
      .then(d => setReviewCount(d.count || 0))
      .catch(() => {});
  }, [location.pathname]);

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h1>RevGuard</h1>
          <p>AI Recovery Controller</p>
        </div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map(item => (
            <div
              key={item.path}
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
              onClick={() => navigate(item.path)}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
              {item.badge && reviewCount > 0 && (
                <span className="nav-badge">{reviewCount}</span>
              )}
            </div>
          ))}
        </nav>
        <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border)' }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            AI handles ambiguity.<br />
            Deterministic handles finance.
          </div>
        </div>
      </aside>
      <main className="main-content fade-in">
        {children}
      </main>
    </div>
  );
}
