import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import Dashboard from './pages/Dashboard';
import Cases from './pages/Cases';
import CaseDetail from './pages/CaseDetail';
import ReviewQueue from './pages/ReviewQueue';
import Metrics from './pages/Metrics';
import './index.css';

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/cases" element={<Cases />} />
          <Route path="/cases/:caseId" element={<CaseDetail />} />
          <Route path="/review" element={<ReviewQueue />} />
          <Route path="/metrics" element={<Metrics />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
