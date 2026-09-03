const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(err.detail || err.error?.message || 'API error');
  }
  return response.json();
}

export const api = {
  getDashboard: () => apiFetch('/api/v1/dashboard/summary'),
  getCases: (params = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => v !== undefined && q.set(k, v));
    return apiFetch(`/api/v1/cases?${q}`);
  },
  getCase: (id) => apiFetch(`/api/v1/cases/${id}`),
  getCaseAudit: (id) => apiFetch(`/api/v1/cases/${id}/audit`),
  getCaseMessage: (id) => apiFetch(`/api/v1/cases/${id}/message`),
  recoverCase: (id) => apiFetch(`/api/v1/cases/${id}/recover`, { method: 'POST' }),
  approveCase: (id) => apiFetch(`/api/v1/cases/${id}/approve`, { method: 'POST' }),
  rejectCase: (id, reason) => apiFetch(`/api/v1/cases/${id}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  }),
  getMetrics: () => apiFetch('/api/v1/metrics'),
  seedDataset: (params) => apiFetch('/api/v1/events/seed', {
    method: 'POST',
    body: JSON.stringify(params),
  }),
  simulateFailure: (type, case_id) => apiFetch('/api/v1/simulate/failure', {
    method: 'POST',
    body: JSON.stringify({ type, case_id }),
  }),
  simulatePitchScenario: () => apiFetch('/api/v1/simulate/pitch-scenario', {
    method: 'POST',
  }),
};

// Formatting helpers
export function formatRupees(paise) {
  const rupees = (paise || 0) / 100;
  return `₹${rupees.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

export function formatDate(ts) {
  if (!ts) return '—';
  return new Date(ts).toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export function policyBadgeClass(decision) {
  switch (decision?.toUpperCase()) {
    case 'AUTO': return 'chip chip-auto';
    case 'QUEUE_FOR_REVIEW': return 'chip chip-review';
    case 'BLOCKED': return 'chip chip-blocked';
    default: return 'chip';
  }
}

export function statusBadgeClass(status) {
  switch (status?.toUpperCase()) {
    case 'RECOVERED': return 'chip chip-recovered';
    case 'ACTION_PENDING':
    case 'ACTION_SENT':
    case 'RECOVERY_PENDING': return 'chip chip-pending';
    case 'QUEUED_FOR_REVIEW': return 'chip chip-review';
    case 'CLOSED':
    case 'REJECTED': return 'chip chip-blocked';
    default: return 'chip chip-pending';
  }
}

export function confidenceColor(conf) {
  if (conf >= 0.85) return 'var(--color-success)';
  if (conf >= 0.60) return 'var(--color-accent)';
  return 'var(--color-danger)';
}
