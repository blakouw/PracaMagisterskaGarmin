import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import type {
  ApiHealthResponse,
  DashboardChatRequest,
  DashboardChatResponse,
  DashboardCurrentState,
  DashboardDisclosures,
  DashboardQualityAndCoverage,
  SnapshotStatus,
  TimeSeriesResponse
} from './dashboardTypes';

@Injectable({ providedIn: 'root' })
export class DashboardApi {
  private readonly http = inject(HttpClient);

  fetchHealth(): Promise<ApiHealthResponse> {
    return this.get<ApiHealthResponse>('/api/v1/health');
  }

  fetchSnapshotStatus(): Promise<SnapshotStatus> {
    return this.get<SnapshotStatus>('/api/v1/snapshot/status');
  }

  fetchCurrentState(): Promise<DashboardCurrentState> {
    return this.get<DashboardCurrentState>('/api/v1/dashboard/current-state');
  }

  fetchTimeSeries(filters: { limit?: number | 'all'; date_from?: string; date_to?: string } = {}): Promise<TimeSeriesResponse> {
    let params = new HttpParams();
    if (filters.limit && filters.limit !== 'all') params = params.set('limit', filters.limit);
    if (filters.date_from) params = params.set('date_from', filters.date_from);
    if (filters.date_to) params = params.set('date_to', filters.date_to);
    return this.get<TimeSeriesResponse>('/api/v1/dashboard/time-series', params);
  }

  fetchQualityAndCoverage(): Promise<DashboardQualityAndCoverage> {
    return this.get<DashboardQualityAndCoverage>('/api/v1/dashboard/quality');
  }

  fetchDisclosures(): Promise<DashboardDisclosures> {
    return this.get<DashboardDisclosures>('/api/v1/dashboard/disclosures');
  }

  sendDashboardChatMessage(payload: DashboardChatRequest): Promise<DashboardChatResponse> {
    return firstValueFrom(this.http.post<DashboardChatResponse>('/api/v1/dashboard/chat', payload));
  }

  private get<T>(path: string, params?: HttpParams): Promise<T> {
    return firstValueFrom(this.http.get<T>(path, { params }));
  }
}
