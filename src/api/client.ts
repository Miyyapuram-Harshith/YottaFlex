import {
  HealthResponse,
  OverviewResponse,
  KpiDefinitionsResponse,
  AnomalyResponse,
  TableQueryResponse,
  LedgerVerifyResponse,
  AdjudicatePayload,
  AdjudicateResponse,
  CalculateRefundPayload,
  CalculateRefundResponse
} from './types';

const API_BASE = '/api';

export function getDemoIdentity(): { role: string; id: string } {
  try {
    const saved = localStorage.getItem('yottaflex_demo_identity');
    if (saved) {
      return JSON.parse(saved);
    }
  } catch {
    // fallback
  }
  return { role: 'OPERATOR', id: 'OP-1042' };
}

export function setDemoIdentity(role: string, id: string) {
  try {
    localStorage.setItem('yottaflex_demo_identity', JSON.stringify({ role, id }));
  } catch {
    // ignore
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const identity = getDemoIdentity();
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  headers.set('X-Actor-Role', identity.role);
  headers.set('X-Actor-Id', identity.id);

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson.error?.message) {
        errorDetail = errJson.error.message;
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

export const api = {
  getHealth: () => request<HealthResponse>('/health'),
  getOverview: () => request<OverviewResponse>('/overview'),
  getKpiDefinitions: () => request<KpiDefinitionsResponse>('/meta/kpi-definitions'),
  getAnomalies: () => request<AnomalyResponse>('/anomalies'),
  getLedgerVerify: () => request<LedgerVerifyResponse>('/ledger/verify'),
  getTable: <T = Record<string, unknown>>(tableName: string, page = 1, limit = 25, search = '') =>
    request<TableQueryResponse<T>>(`/tables/${tableName}?page=${page}&limit=${limit}&search=${encodeURIComponent(search)}`),
  getEntity: (entityType: string, entityId: string) =>
    request<{ entity_type: string; entity_id: string; events: Record<string, unknown>[]; record?: Record<string, unknown> }>(`/entity/${entityType}/${entityId}`),
  getSummary: () => request<Record<string, unknown>>('/summary'),
  adjudicate: (payload: AdjudicatePayload) =>
    request<AdjudicateResponse>('/adjudicate', { method: 'POST', body: JSON.stringify(payload) }),
  calculateRefund: (payload: CalculateRefundPayload) =>
    request<CalculateRefundResponse>('/calculate-refund', { method: 'POST', body: JSON.stringify(payload) }),
};

