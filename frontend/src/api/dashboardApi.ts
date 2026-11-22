import type {
  ApiHealthResponse,
  DashboardCurrentState,
  DashboardDisclosures,
  DashboardQualityAndCoverage,
  SnapshotStatus,
  TimeSeriesResponse,
  DashboardChatRequest,
  DashboardChatResponse
} from './dashboardTypes';

export class ApiError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.payload = payload;
  }
}

async function requestJson<T>(path: string): Promise<T> {
  const response = await fetch(path, { method: 'GET' });
  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  if (!response.ok) {
    throw new ApiError(`Request failed with HTTP ${response.status}`, response.status, payload);
  }
  return payload as T;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  if (!response.ok) {
    throw new ApiError(`Request failed with HTTP ${response.status}`, response.status, payload);
  }
  return payload as T;
}

export function fetchHealth(): Promise<ApiHealthResponse> {
  return requestJson<ApiHealthResponse>('/api/v1/health');
}

export function fetchSnapshotStatus(): Promise<SnapshotStatus> {
  return requestJson<SnapshotStatus>('/api/v1/snapshot/status');
}

export function fetchCurrentState(): Promise<DashboardCurrentState> {
  return requestJson<DashboardCurrentState>('/api/v1/dashboard/current-state');
}

export function fetchTimeSeries(params?: { limit?: number | 'all'; date_from?: string; date_to?: string }): Promise<TimeSeriesResponse> {
  const search = new URLSearchParams();
  if (params?.limit && params.limit !== 'all') search.set('limit', String(params.limit));
  if (params?.date_from) search.set('date_from', params.date_from);
  if (params?.date_to) search.set('date_to', params.date_to);
  const suffix = search.toString() ? `?${search.toString()}` : '';
  return requestJson<TimeSeriesResponse>(`/api/v1/dashboard/time-series${suffix}`);
}

export function fetchQualityAndCoverage(): Promise<DashboardQualityAndCoverage> {
  return requestJson<DashboardQualityAndCoverage>('/api/v1/dashboard/quality');
}

export function fetchDisclosures(): Promise<DashboardDisclosures> {
  return requestJson<DashboardDisclosures>('/api/v1/dashboard/disclosures');
}


export function sendDashboardChatMessage(payload: DashboardChatRequest): Promise<DashboardChatResponse> {
  return postJson<DashboardChatResponse>('/api/v1/dashboard/chat', payload);
}
