import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';
import Cases from './pages/Cases';
import CaseDetail from './pages/CaseDetail';
import ReviewQueue from './pages/ReviewQueue';
import Metrics from './pages/Metrics';
import Docs from './pages/Docs';
import './index.css';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Standalone Full-Width Landing Page */}
        <Route path="/" element={<LandingPage />} />

        {/* Cockpit & Operational App wrapped in Layout */}
        <Route path="/cockpit" element={<Layout><Dashboard /></Layout>} />
        <Route path="/dashboard" element={<Layout><Dashboard /></Layout>} />
        <Route path="/cases" element={<Layout><Cases /></Layout>} />
        <Route path="/cases/:caseId" element={<Layout><CaseDetail /></Layout>} />
        <Route path="/review" element={<Layout><ReviewQueue /></Layout>} />
        <Route path="/metrics" element={<Layout><Metrics /></Layout>} />
        <Route path="/docs" element={<Layout><Docs /></Layout>} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
