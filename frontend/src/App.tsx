import { useEffect, useState } from 'react';
import {
  fetchCurrentState,
  fetchDisclosures,
  fetchHealth,
  fetchQualityAndCoverage,
  fetchSnapshotStatus,
  fetchTimeSeries
} from './api/dashboardApi';
import type {
  ApiHealthResponse,
  DashboardCurrentState,
  DashboardDisclosures,
  DashboardQualityAndCoverage,
  SnapshotStatus,
  TimeSeriesRecord
} from './api/dashboardTypes';
import { AppStatusHeader } from './components/AppStatusHeader';
import { DashboardChatPanel } from './components/DashboardChatPanel';
import { DeterministicWeightsPanel } from './components/DeterministicWeightsPanel';
import { ErrorState } from './components/ErrorState';
import { LoadingState } from './components/LoadingState';
import { LoadMetricsPanel } from './components/LoadMetricsPanel';
import { OptionalAssistedPwsCard } from './components/OptionalAssistedPwsCard';
import { PrimaryPwsCard } from './components/PrimaryPwsCard';
import { PwsComponentInputsPanel } from './components/PwsComponentInputsPanel';
import { PwsComponentsPanel } from './components/PwsComponentsPanel';
import { PwsModelComparisonPanel } from './components/PwsModelComparisonPanel';
import { QualityCoveragePanel } from './components/QualityCoveragePanel';
import { VariableTrendsPanel } from './components/VariableTrendsPanel';

type Range = 7 | 30 | 90 | 'all';

interface DashboardState {
  health: ApiHealthResponse | null;
  status: SnapshotStatus | null;
  current: DashboardCurrentState | null;
  timeSeries: TimeSeriesRecord[];
  quality: DashboardQualityAndCoverage | null;
  disclosures: DashboardDisclosures | null;
  loading: boolean;
  fatal: 'api' | 'snapshot' | null;
  sectionErrors: Record<string, string>;
  range: Range;
}

const initialState: DashboardState = {
  health: null,
  status: null,
  current: null,
  timeSeries: [],
  quality: null,
  disclosures: null,
  loading: true,
  fatal: null,
  sectionErrors: {},
  range: 30
};

export default function App() {
  const [state, setState] = useState<DashboardState>(initialState);

  async function loadDashboard(range: Range = state.range) {
    setState((current) => ({ ...current, loading: true, range }));
    try {
      const health = await fetchHealth();
      if (!health.snapshot_available) {
        setState({ ...initialState, loading: false, fatal: 'snapshot', health, range });
        return;
      }
      const [status, current] = await Promise.all([fetchSnapshotStatus(), fetchCurrentState()]);
      const sectionErrors: Record<string, string> = {};
      let timeSeries: TimeSeriesRecord[] = [];
      let quality: DashboardQualityAndCoverage | null = null;
      let disclosures: DashboardDisclosures | null = null;
      try {
        const response = await fetchTimeSeries({ limit: range });
        timeSeries = response.records;
      } catch {
        sectionErrors.timeSeries = 'Szereg czasowy jest niedostępny z lokalnego API.';
      }
      try {
        quality = await fetchQualityAndCoverage();
      } catch {
        sectionErrors.quality = 'Dane jakości i pokrycia są niedostępne z lokalnego API.';
      }
      try {
        disclosures = await fetchDisclosures();
      } catch {
        sectionErrors.disclosures = 'Informacje opisowe są niedostępne z lokalnego API.';
      }
      setState({ health, status, current, timeSeries, quality, disclosures, loading: false, fatal: null, sectionErrors, range });
    } catch {
      setState({ ...initialState, loading: false, fatal: 'api', range });
    }
  }

  useEffect(() => {
    void loadDashboard(30);
  }, []);

  if (state.loading) return <LoadingState />;
  if (state.fatal === 'api') return <ErrorState kind="api" />;
  if (state.fatal === 'snapshot' || !state.health?.snapshot_available) return <ErrorState kind="snapshot" />;
  if (!state.health || !state.current) return <ErrorState kind="api" detail="Wymagane sekcje dashboardu są niedostępne." />;

  return (
    <main className="shell">
      <AppStatusHeader />
      <section className="hero-grid">
        <PrimaryPwsCard primary={state.current.primary_pws} />
        <OptionalAssistedPwsCard assisted={state.current.optional_assisted_pws} />
      </section>
      <section className="dashboard-grid">
        <PwsComponentsPanel components={state.current.pws_components} />
        <DeterministicWeightsPanel weights={state.current.pws_weights} />
        <LoadMetricsPanel metrics={state.current.load_metrics} />
      </section>
      <PwsModelComparisonPanel
        records={state.timeSeries}
        primary={state.current.primary_pws}
        localAssisted={state.current.optional_assisted_pws}
        externalAssisted={state.current.external_assisted_pws}
        range={state.range}
        onRangeChange={(range) => void loadDashboard(range)}
        error={state.sectionErrors.timeSeries}
      />
      <VariableTrendsPanel records={state.timeSeries} />
      <DashboardChatPanel current={state.current} snapshotStatus={state.status} quality={state.quality} disclosures={state.disclosures} />
      <section className="dashboard-grid">
        <QualityCoveragePanel coverage={state.current.coverage} quality={state.quality} error={state.sectionErrors.quality} />
      </section>
      <PwsComponentInputsPanel records={state.timeSeries} />
    </main>
  );
}
