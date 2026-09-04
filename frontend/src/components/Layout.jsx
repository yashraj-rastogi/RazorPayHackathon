import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { api } from '../api';

const NAV_ITEMS = [
  { path: '/cockpit', label: 'Cockpit', icon: '⚡' },
  { path: '/cases', label: 'Cases Ledger', icon: '📋' },
  { path: '/review', label: 'Review Queue', icon: '👁', badge: true },
  { path: '/metrics', label: 'Evaluation', icon: '📈' },
  { path: '/docs', label: 'Docs & Arch', icon: '📖' },
  { path: '/', label: 'Product Home', icon: '🌐' },
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
    <div className="app-layout bg-grid">
      {/* Desktop Side Rail */}
      <aside className="side-rail">
        <div className="rail-header" onClick={() => navigate('/cockpit')} style={{ cursor: 'pointer' }}>
          <div className="rail-logo">⚡</div>
          <div className="rail-brand">
            <span className="rail-brand-title">RevGuard</span>
            <span className="rail-brand-sub">TACTICAL CONTROLLER</span>
          </div>
        </div>

        <nav className="rail-nav">
          {NAV_ITEMS.map(item => {
            const isActive = location.pathname === item.path || (item.path === '/cockpit' && location.pathname === '/dashboard');
            return (
              <div
                key={item.path}
                className={`nav-item ${isActive ? 'active' : ''}`}
                onClick={() => navigate(item.path)}
              >
                <span style={{ fontSize: '16px' }}>{item.icon}</span>
                <span>{item.label}</span>
                {item.badge && reviewCount > 0 && (
                  <span className="notif-badge">{reviewCount}</span>
                )}
              </div>
            );
          })}
        </nav>

        <div className="rail-footer">
          <div className="rail-footer-badge">
            <span className="rail-footer-pulse" />
            <span>OPERATOR ACTIVE</span>
          </div>
          <div>POLICY ENGINE // v1.0</div>
        </div>
      </aside>

      {/* Mobile Top Header */}
      <header className="mobile-header">
        <div className="mobile-header-brand" onClick={() => navigate('/cockpit')} style={{ cursor: 'pointer' }}>
          <div className="rail-logo" style={{ width: 28, height: 28, fontSize: 14 }}>⚡</div>
          <span className="mobile-title">RevGuard</span>
        </div>
        {reviewCount > 0 && (
          <span className="notif-badge" onClick={() => navigate('/review')}>
            {reviewCount}
          </span>
        )}
      </header>

      {/* Main Routed Content */}
      <main className="main-content fade-in">
        <div className="screen-container">
          {children}
        </div>
      </main>

      {/* Mobile Bottom Tab Bar */}
      <nav className="bottom-tab-bar">
        {NAV_ITEMS.map(item => {
          const isActive = location.pathname === item.path || (item.path === '/cockpit' && location.pathname === '/dashboard');
          return (
            <div
              key={item.path}
              className={`tab-bar-item ${isActive ? 'active' : ''}`}
              onClick={() => navigate(item.path)}
            >
              <span style={{ fontSize: '18px' }}>{item.icon}</span>
              <span>{item.label}</span>
            </div>
          );
        })}
      </nav>
    </div>
  );
}
