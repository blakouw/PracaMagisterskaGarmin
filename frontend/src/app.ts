import { Component, inject, signal, type OnInit } from '@angular/core';
import { DashboardApi } from './api/dashboardApi';
import type { DashboardCurrentState, DashboardQualityAndCoverage, SnapshotStatus, TimeSeriesRecord } from './api/dashboardTypes';
import { AppStatusHeader } from './components/app-status-header';
import { DashboardChatPanel } from './components/dashboard-chat-panel';
import { DeterministicWeightsPanel } from './components/deterministic-weights-panel';
import { ErrorState } from './components/error-state';
import { LoadingState } from './components/loading-state';
import { LoadMetricsPanel } from './components/load-metrics-panel';
import { OptionalAssistedPwsCard } from './components/optional-assisted-pws-card';
import { PrimaryPwsCard } from './components/primary-pws-card';
import { PwsComponentInputsPanel } from './components/pws-component-inputs-panel';
import { PwsComponentsPanel } from './components/pws-components-panel';
import { PwsModelComparisonPanel, type DashboardRange } from './components/pws-model-comparison-panel';
import { QualityCoveragePanel } from './components/quality-coverage-panel';
import { VariableTrendsPanel } from './components/variable-trends-panel';

type DashboardView =
  | { kind: 'loading' }
  | { kind: 'error'; error: 'api' | 'snapshot'; detail?: string }
  | {
      kind: 'ready';
      current: DashboardCurrentState;
      status: SnapshotStatus;
      records: TimeSeriesRecord[];
      quality: DashboardQualityAndCoverage | null;
      range: DashboardRange;
      seriesError?: string;
      qualityError?: string;
      disclosuresError?: string;
    };

@Component({
  selector: 'app-dashboard',
  imports: [
    AppStatusHeader, DashboardChatPanel, DeterministicWeightsPanel, ErrorState, LoadingState,
    LoadMetricsPanel, OptionalAssistedPwsCard, PrimaryPwsCard, PwsComponentInputsPanel,
    PwsComponentsPanel, PwsModelComparisonPanel, QualityCoveragePanel, VariableTrendsPanel
  ],
  templateUrl: './app.html'
})
export class AppComponent implements OnInit {
  private readonly api = inject(DashboardApi);
  protected readonly view = signal<DashboardView>({ kind: 'loading' });

  ngOnInit(): void {
    void this.loadDashboard(30);
  }

  protected changeRange(range: DashboardRange): void {
    if (this.view().kind === 'ready') void this.loadDashboard(range);
  }

  private async loadDashboard(range: DashboardRange): Promise<void> {
    this.view.set({ kind: 'loading' });
    try {
      const health = await this.api.fetchHealth();
      if (!health.snapshot_available) {
        this.view.set({ kind: 'error', error: 'snapshot' });
        return;
      }

      const [status, current] = await Promise.all([
        this.api.fetchSnapshotStatus(),
        this.api.fetchCurrentState()
      ]);
      if (!current) {
        this.view.set({ kind: 'error', error: 'api', detail: 'Wymagane sekcje dashboardu są niedostępne.' });
        return;
      }

      const next: Extract<DashboardView, { kind: 'ready' }> = {
        kind: 'ready', status, current, range, records: [], quality: null
      };
      try {
        next.records = (await this.api.fetchTimeSeries({ limit: range })).records;
      } catch {
        next.seriesError = 'Szereg czasowy jest niedostępny z lokalnego API.';
      }
      try {
        next.quality = await this.api.fetchQualityAndCoverage();
      } catch {
        next.qualityError = 'Dane jakości i pokrycia są niedostępne z lokalnego API.';
      }
      try {
        await this.api.fetchDisclosures();
      } catch {
        next.disclosuresError = 'Informacje opisowe są niedostępne z lokalnego API.';
      }

      this.view.set(next);
    } catch {
      this.view.set({ kind: 'error', error: 'api' });
    }
  }
}
