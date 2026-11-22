import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, describe, expect, test } from 'vitest';
import { DashboardApi } from './dashboardApi';

describe('local dashboard API contract', () => {
  let api: DashboardApi;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    api = TestBed.inject(DashboardApi);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
    TestBed.resetTestingModule();
  });

  test.each([
    ['fetchHealth', '/api/v1/health'],
    ['fetchSnapshotStatus', '/api/v1/snapshot/status'],
    ['fetchCurrentState', '/api/v1/dashboard/current-state'],
    ['fetchQualityAndCoverage', '/api/v1/dashboard/quality'],
    ['fetchDisclosures', '/api/v1/dashboard/disclosures']
  ] as const)('sends %s to the relative GET endpoint', async (method, url) => {
    const result = api[method]();
    http.expectOne({ url, method: 'GET' }).flush({});
    await expect(result).resolves.toEqual({});
  });

  test('preserves bounded time-series ranges and date filters', async () => {
    const response = api.fetchTimeSeries({ limit: 7, date_from: '2026-05-20', date_to: '2026-05-22' });
    const request = http.expectOne({
      url: '/api/v1/dashboard/time-series?limit=7&date_from=2026-05-20&date_to=2026-05-22',
      method: 'GET'
    });
    request.flush({ records: [] });
    await expect(response).resolves.toEqual({ records: [] });
  });

  test('requests the whole time series without a limit', async () => {
    const response = api.fetchTimeSeries({ limit: 'all' });
    http.expectOne({ url: '/api/v1/dashboard/time-series', method: 'GET' }).flush({ records: [] });
    await response;
  });

  test('posts the original chat message and history to the local API', async () => {
    const payload = { message: 'Pokaż PWS', history: [{ role: 'assistant' as const, content: 'Cześć' }] };
    const response = api.sendDashboardChatMessage(payload);
    const request = http.expectOne({ url: '/api/v1/dashboard/chat', method: 'POST' });
    expect(request.request.body).toEqual(payload);
    request.flush({ answer: 'PWS' });
    await expect(response).resolves.toEqual({ answer: 'PWS' });
  });
});
