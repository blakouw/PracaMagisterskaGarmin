import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, test, vi } from 'vitest';
import App from './App';
import type { ApiHealthResponse, DashboardCurrentState, DashboardQualityAndCoverage, SnapshotStatus, TimeSeriesResponse } from './api/dashboardTypes';

const healthOk: ApiHealthResponse = {
  service: 'dashboard_snapshot_api',
  api_version: 'v1',
  status: 'ok',
  local_only: true,
  read_only: true,
  snapshot_available: true,
  snapshot_id: 'dashboard_2026-05-22_20260523T141527123456Z',
  latest_data_date: '2026-05-22',
  primary_score_type: 'deterministic',
  optional_assisted_score_available: false
};

const snapshotStatus: SnapshotStatus = {
  snapshot_id: 'dashboard_2026-05-22_20260523T141527123456Z',
  latest_data_date: '2026-05-22',
  payload_ready: true,
  primary_pws: {
    score_type: 'deterministic',
    computed: true,
    score: 78.42,
    label_id: 'balanced',
    label: 'stabilny',
    coverage_tier: 'full'
  },
  optional_assisted_pws: {
    available: false,
    must_not_replace_primary_score: true
  },
  records_count: 3
};

function currentState(overrides: Partial<DashboardCurrentState> = {}): DashboardCurrentState {
  return {
    date: '2026-05-22',
    primary_pws: {
      score_type: 'deterministic',
      score_field: 'pws_deterministic',
      score: 78.42,
      computed: true,
      status: 'computed_full_coverage',
      label_id: 'balanced',
      label: 'stabilny',
      coverage_ratio: 1,
      coverage_tier: 'full',
      computed_from_partial_coverage: false,
      available_components: ['LQ', 'REC', 'CAP', 'VS'],
      missing_components: [],
      display_disclosure: 'Primary deterministic PWS calculated upstream.'
    },
    optional_assisted_pws: {
      available: false,
      computed: false,
      status: 'not_available_no_assisted_artifact',
      must_not_replace_primary_score: true,
      display_disclosure: 'Optional analysis has not been executed.'
    },
    readiness: {
      score: 86.76,
      computed: true,
      status: 'computed',
      label_id: 'high',
      label: 'wysoka',
      coverage_ratio: 1,
      available_components: ['sleep', 'hrv'],
      missing_components: []
    },
    pws_components: {
      LQ: { name: 'Load Quality', score: 72, status: 'computed' },
      REC: { name: 'Recovery', score: 84, status: 'computed' },
      CAP: { name: 'Capacity', score: 91, status: 'computed' },
      VS: { name: 'Vital Stability', score: 70, status: 'computed' },
      available_components: ['LQ', 'REC', 'CAP', 'VS'],
      missing_components: [],
      coverage_ratio: 1
    },
    pws_weights: {
      deterministic_effective_weights: { LQ: 0.21, REC: 0.34, CAP: 0.14, VS: 0.31 },
      weights_ready_for_final_pws: true,
      weights_readiness_status: 'ready'
    },
    load_metrics: {
      acwr_ewma: 1.08,
      acwr_rolling: 1.12,
      acute_ewma_7d: 3120.5,
      chronic_ewma_28d: 2889.3,
      monotony_7d: 3.42,
      strain_7d: 14210.5
    },
    coverage: {
      pws_coverage_tier: 'full',
      pws_coverage_ratio: 1,
      pws_computed_from_partial_coverage: false,
      readiness_coverage_ratio: 1,
      pws_components_coverage_ratio: 1,
      missing_pws_components: [],
      missing_readiness_components: []
    },
    disclosures: [
      'Deterministic PWS is the primary auditable score.',
      'Optional LLM-assisted PWS, when available, is a separate comparison variant and never replaces deterministic PWS.',
      'Missing values remain null and are not replaced with zero.'
    ],
    ...overrides
  };
}

const timeSeries: TimeSeriesResponse = {
  snapshot_id: healthOk.snapshot_id!,
  filters: { limit: 30 },
  records_count: 3,
  records: [
    { date: '2026-05-20', pws_deterministic: 70, readiness_score: 80, lq_score: 60, rec_score: 70, cap_score: 80, vs_score: 90, optional_assisted_pws: 71.1, external_assisted_pws: 69.8, acwr_ewma: 1.05, strain_7d: 3600, weight_lq: 0.21, weight_rec: 0.34, weight_cap: 0.15, weight_vs: 0.3, local_llm_weight_lq: 0.2, local_llm_weight_rec: 0.31, local_llm_weight_cap: 0.19, local_llm_weight_vs: 0.3, openai_weight_lq: 0.19, openai_weight_rec: 0.29, openai_weight_cap: 0.22, openai_weight_vs: 0.3 },
    { date: '2026-05-21', pws_deterministic: null, readiness_score: 82, lq_score: null, rec_score: 71, cap_score: 81, vs_score: 91, optional_assisted_pws: null, external_assisted_pws: null, acwr_ewma: 0.84, strain_7d: 4100, weight_lq: 0.22, weight_rec: 0.33, weight_cap: 0.15, weight_vs: 0.3, local_llm_weight_lq: null, openai_weight_lq: null },
    { date: '2026-05-22', pws_deterministic: 78.42, readiness_score: 86.76, lq_score: 72, rec_score: 84, cap_score: 91, vs_score: 70, optional_assisted_pws: 79.05, external_assisted_pws: 80.2, acwr_ewma: 0.61, strain_7d: 3800, weight_lq: 0.23, weight_rec: 0.32, weight_cap: 0.15, weight_vs: 0.3, local_llm_weight_lq: 0.21, local_llm_weight_rec: 0.29, local_llm_weight_cap: 0.2, local_llm_weight_vs: 0.3, openai_weight_lq: 0.2, openai_weight_rec: 0.27, openai_weight_cap: 0.24, openai_weight_vs: 0.29 }
  ]
};

const quality: DashboardQualityAndCoverage = {
  records_count: 3,
  presentation_availability: {
    primary_pws_computed_count: 2,
    primary_pws_unavailable_count: 1,
    optional_assisted_score_count: 0,
    current_state_primary_pws_available: true,
    current_state_optional_assisted_pws_available: false
  },
  coverage_tiers: { full: 1, partial_eligible: 1, insufficient: 1 },
  component_availability: {
    LQ: { available_count: 2, coverage_ratio: 0.67 },
    REC: { available_count: 3, coverage_ratio: 1 },
    CAP: { available_count: 3, coverage_ratio: 1 },
    VS: { available_count: 3, coverage_ratio: 1 }
  }
};

const disclosures = {
  primary_score: 'Deterministic PWS is the primary auditable product score.',
  medical_limitation: 'PWS and related metrics are not medical diagnoses, injury predictions or professional training prescriptions.',
  privacy: 'The payload contains private derived health and training information and must remain local.'
};

function mockApi(current: DashboardCurrentState = currentState(), health: ApiHealthResponse = healthOk) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.startsWith('/api/v1/health')) return Response.json(health);
    if (url.startsWith('/api/v1/snapshot/status')) return Response.json(snapshotStatus);
    if (url.startsWith('/api/v1/dashboard/current-state')) return Response.json(current);
    if (url.startsWith('/api/v1/dashboard/time-series')) return Response.json(timeSeries);
    if (url.startsWith('/api/v1/dashboard/quality')) return Response.json(quality);
    if (url.startsWith('/api/v1/dashboard/disclosures')) return Response.json(disclosures);
    if (url.startsWith('/api/v1/dashboard/chat')) return Response.json({ answer: 'LLM answer: readiness is available for 2026-05-22.', llm_called: true, persisted: false, snapshot_modified: false, pipeline_triggered: false, tools_used: ['dashboard_current_state'] });
    return Response.json({ error: 'not found' }, { status: 404 });
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe('local dashboard UI', () => {
  test('renders loading state', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})));
    render(<App />);
    expect(screen.getByText('Ładowanie lokalnego dashboardu')).toBeInTheDocument();
  });

  test('renders API unavailable state', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => Promise.reject(new Error('offline'))));
    render(<App />);
    expect(await screen.findByText('Lokalne API dashboardu jest niedostępne')).toBeInTheDocument();
  });

  test('renders snapshot unavailable state', async () => {
    mockApi(currentState(), { ...healthOk, status: 'degraded', snapshot_available: false });
    render(<App />);
    expect(await screen.findByText('Brak poprawnego opublikowanego snapshotu dashboardu')).toBeInTheDocument();
  });

  test('renders primary deterministic PWS and does not promote assisted score', async () => {
    mockApi(currentState({
      optional_assisted_pws: {
        available: true,
        score_type: 'llm_assisted',
        score: 77.89,
        computed: true,
        status: 'available_validated_assisted_variant',
        label: 'stabilny',
        delta_from_deterministic: -0.53,
        validated_adjusted_weights: { LQ: 0.2, REC: 0.34, CAP: 0.13, VS: 0.33 },
        must_not_replace_primary_score: true
      }
    }));
    render(<App />);
    const primary = await screen.findByLabelText('Główny deterministyczny PWS');
    expect(within(primary).getByText('Deterministyczny PWS')).toBeInTheDocument();
    expect(within(primary).getByText('78,42')).toBeInTheDocument();
    const assisted = screen.getByLabelText('Opcjonalny wariant PWS asystowany przez LLM');
    expect(within(assisted).getByText('PWS asystowany przez LLM')).toBeInTheDocument();
    expect(within(assisted).getByText('77,89')).toBeInTheDocument();
    expect(within(assisted).getByText('Ten wariant nie zastępuje deterministycznego PWS.')).toBeInTheDocument();
  });

  test('renders unavailable assisted status separately', async () => {
    mockApi();
    render(<App />);
    expect(await screen.findByText('Brak wariantu asystowanego')).toBeInTheDocument();
    expect(screen.getByText('Analiza LLM nie została uruchomiona')).toBeInTheDocument();
  });

  test('renders no score without numeric zero for insufficient coverage', async () => {
    mockApi(currentState({
      primary_pws: {
        score_type: 'deterministic',
        score_field: 'pws_deterministic',
        score: null,
        computed: false,
        status: 'not_computed_insufficient_component_coverage',
        label_id: 'insufficient_data',
        label: 'insufficient_data',
        coverage_ratio: 0.5,
        coverage_tier: 'insufficient',
        available_components: ['LQ', 'VS'],
        missing_components: ['REC', 'CAP']
      },
      coverage: {
        pws_coverage_tier: 'insufficient',
        pws_coverage_ratio: 0.5,
        pws_computed_from_partial_coverage: false,
        missing_pws_components: ['REC', 'CAP'],
        missing_readiness_components: []
      }
    }));
    render(<App />);
    const primary = await screen.findByLabelText('Główny deterministyczny PWS');
    expect(within(primary).getAllByText('Brak wyniku').length).toBeGreaterThan(0);
    expect(within(primary).getByText('Niewystarczające pokrycie komponentów')).toBeInTheDocument();
    expect(within(primary).queryByText('0')).not.toBeInTheDocument();
  });

  test('renders full and partial coverage badges and missing components', async () => {
    mockApi(currentState({
      primary_pws: {
        ...currentState().primary_pws,
        coverage_tier: 'partial_eligible',
        coverage_ratio: 0.75,
        computed_from_partial_coverage: true,
        missing_components: ['CAP']
      },
      coverage: {
        pws_coverage_tier: 'partial_eligible',
        pws_coverage_ratio: 0.75,
        pws_computed_from_partial_coverage: true,
        missing_pws_components: ['CAP'],
        missing_readiness_components: []
      }
    }));
    render(<App />);
    expect((await screen.findAllByText('Częściowe pokrycie')).length).toBeGreaterThan(0);
    expect(screen.getByText('Wynik policzono z dopuszczalnego, ale niepełnego zestawu komponentów.')).toBeInTheDocument();
    expect(screen.getByText('Brakujące komponenty PWS: CAP')).toBeInTheDocument();
  });

  test('renders components, weights and load metrics without the removed readiness summary', async () => {
    mockApi();
    render(<App />);
    await screen.findByText('Wagi deterministyczne');
    expect(screen.queryByText('Aktualny stan')).not.toBeInTheDocument();
    expect(screen.getAllByText('Jakość obciążenia').length).toBeGreaterThan(0);
    expect(screen.getByText('Wagi deterministyczne')).toBeInTheDocument();
    expect(screen.getByText('Metryki obciążenia')).toBeInTheDocument();
    expect(screen.queryByText('Status: ready')).not.toBeInTheDocument();
    expect(screen.queryByText('Metryki obciążenia są kontekstem analitycznym i nie są prognozą kontuzji.')).not.toBeInTheDocument();
  });

  test('moves range selection into model comparison and removes the standalone trend panel', async () => {
    const fetchMock = mockApi();
    render(<App />);
    const controls = await screen.findByRole('group', { name: 'Zakres porównania modeli' });
    expect(screen.queryByLabelText('Panel szeregu czasowego')).not.toBeInTheDocument();
    await userEvent.click(within(controls).getByText('7 dni'));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith('/api/v1/dashboard/time-series?limit=7', { method: 'GET' }));
    const refreshedControls = await screen.findByRole('group', { name: 'Zakres porównania modeli' });
    await userEvent.click(within(refreshedControls).getByText('Całość'));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith('/api/v1/dashboard/time-series', { method: 'GET' }));
  });

  test('renders separate deterministic, local LLM and OpenAI weight histories', async () => {
    mockApi();
    render(<App />);
    const deterministic = await screen.findByLabelText('Wagi deterministyczne PWS w czasie');
    const local = screen.getByLabelText('Wagi lokalnego LLM w czasie');
    const openai = screen.getByLabelText('Wagi OpenAI w czasie');
    expect(within(deterministic).getByText(/wariant deterministyczny/)).toBeInTheDocument();
    expect(within(local).getByText(/lokalny LLM/)).toBeInTheDocument();
    expect(within(openai).getByText(/OpenAI/)).toBeInTheDocument();
    expect(screen.queryByText(/^Zakres /)).not.toBeInTheDocument();
  });

  test('renders quality coverage and omits disclosures section', async () => {
    mockApi();
    render(<App />);
    expect(await screen.findByText('Jakość i pokrycie')).toBeInTheDocument();
    expect(screen.queryByText('Disclosures')).not.toBeInTheDocument();
    expect(screen.queryByText('Limitations')).not.toBeInTheDocument();
    expect(screen.getByText(/Brakujące komponenty PWS/)).toBeInTheDocument();
    const computedMetric = screen.getByText('Dni z policzonym PWS').closest('.metric');
    const unavailableMetric = screen.getByText('Dni bez PWS').closest('.metric');
    expect(computedMetric).not.toBeNull();
    expect(unavailableMetric).not.toBeNull();
    expect(within(computedMetric as HTMLElement).getByText('2')).toBeInTheDocument();
    expect(within(unavailableMetric as HTMLElement).getByText('1')).toBeInTheDocument();
  });

  test('compares deterministic, local LLM and external OpenAI PWS over time', async () => {
    mockApi(currentState({
      optional_assisted_pws: {
        available: true,
        score_type: 'llm_assisted',
        score: 79.05,
        computed: true,
        status: 'available_validated_assisted_variant',
        must_not_replace_primary_score: true
      },
      external_assisted_pws: {
        available: true,
        score_type: 'external_llm_assisted',
        score: 80.2,
        computed: true,
        status: 'available_validated_assisted_variant',
        provider: 'openai',
        model: 'test-external-model',
        must_not_replace_primary_score: true,
        must_not_replace_local_llm_variant: true
      }
    }));
    render(<App />);
    const panel = await screen.findByLabelText('Porównanie wariantów PWS w czasie');
    expect(within(panel).getByText('Deterministyczny, lokalny LLM i model zewnętrzny')).toBeInTheDocument();
    expect(within(panel).getByText('OpenAI · test-external-model')).toBeInTheDocument();
    expect(within(panel).queryByText('Wynik główny: deterministyczny')).not.toBeInTheDocument();
    expect(within(panel).getByText('2026-05-22')).toBeInTheDocument();
    expect(within(panel).getByText('80,2')).toBeInTheDocument();
    expect(within(panel).getByText('Odchylenie od wyniku deterministycznego')).toBeInTheDocument();
    expect(panel.querySelector('.chart-range-badge')).toBeNull();
  });

  test('renders validated no-adjustment assisted PWS as ready analysis', async () => {
    mockApi(currentState({
      optional_assisted_pws: {
        available: true,
        score_type: 'llm_assisted',
        score: 78.42,
        computed: true,
        status: 'available_no_adjustment_same_as_deterministic',
        analysis_status: 'available_no_adjustment_same_as_deterministic',
        label: 'stabilny',
        delta_from_deterministic: 0,
        validated_adjusted_weights: { LQ: 0.21, REC: 0.34, CAP: 0.14, VS: 0.31 },
        llm_response_decision: 'no_adjustment',
        llm_reason_summary: 'The deterministic weights are already appropriate.',
        llm_tool_execution: { tool_name: 'persist_llm_assisted_pws_record', attempted: true, succeeded: true, error: null },
        must_not_replace_primary_score: true
      }
    }));
    render(<App />);
    const assisted = await screen.findByLabelText('Opcjonalny wariant PWS asystowany przez LLM');
    expect(within(assisted).getByText('Analiza PWS asystowana przez LLM jest gotowa.')).toBeInTheDocument();
    expect(within(assisted).getByText('78,42')).toBeInTheDocument();
    expect(within(assisted).getByText(/ograniczona zmiana wag/)).toBeInTheDocument();
    expect(within(assisted).getByText('Zapis wyniku: udany')).toBeInTheDocument();
  });

  test('renders visible error when LLM did not deliver assisted PWS values', async () => {
    mockApi(currentState({
      optional_assisted_pws: {
        available: false,
        computed: false,
        status: 'error_llm_no_assisted_score_delivered',
        llm_error: 'LLM did not deliver assisted PWS values.',
        llm_tool_execution: { tool_name: 'persist_llm_assisted_pws_record', attempted: true, succeeded: false, error: 'LLM_RESPONSE_NOT_JSON' },
        must_not_replace_primary_score: true
      }
    }));
    render(<App />);
    expect(await screen.findByText('LLM-assisted PWS niedostępny')).toBeInTheDocument();
    expect(screen.getByText('LLM nie dostarczył wartości assisted PWS.')).toBeInTheDocument();
    expect(screen.getByText('Zapis wyniku: nieudany')).toBeInTheDocument();
  });

  test('renders local snapshot chat and answers from dashboard data', async () => {
    mockApi();
    render(<App />);
    expect(await screen.findByLabelText('Panel czatu dashboardu')).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText('Pytanie o dashboard'), 'readiness');
    await userEvent.click(screen.getByText('Wyślij'));
    expect(await screen.findByText(/LLM answer: readiness is available/)).toBeInTheDocument();
  });

  test('omits the requested compact labels and coverage tile', async () => {
    mockApi();
    render(<App />);
    await screen.findByText('Panel Personal Wellness');
    for (const text of [
      'Pełne pokrycie',
      'Osobny wariant',
      'Aktualny stan',
      'Ostatnie dane',
      'Status: ready',
      'Wynik główny: deterministyczny'
    ]) {
      expect(screen.queryByText(text)).not.toBeInTheDocument();
    }
  });

  test('does not render prohibited action buttons', async () => {
    mockApi();
    render(<App />);
    expect(await screen.findByText('Panel Personal Wellness')).toBeInTheDocument();
    for (const text of ['run pipeline', 'sync garmin', 'login', 'edit weights', 'ask llm', 'recommendation']) {
      expect(screen.queryByText(new RegExp(text, 'i'))).not.toBeInTheDocument();
    }
  });
});
