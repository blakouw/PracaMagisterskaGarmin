import { useMemo, useState } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';
import type { TimeSeriesRecord } from '../api/dashboardTypes';

type ComponentId = 'LQ' | 'REC' | 'CAP' | 'VS';
type AxisKind = 'score' | 'ratio' | 'load' | 'hours' | 'distance' | 'bpm' | 'ms' | 'percent' | 'respiration';

type SeriesDef = {
  sourceKey: keyof TimeSeriesRecord;
  chartKey: string;
  label: string;
  unit: string;
  description: string;
  color: string;
  axisKind: AxisKind;
  scale?: 'seconds_to_hours';
};

type ComponentConfig = {
  title: string;
  tabLabel: string;
  summary: string;
  series: SeriesDef[];
};

const componentInputs: Record<ComponentId, ComponentConfig> = {
  LQ: {
    title: 'Jakość obciążenia',
    tabLabel: 'Obciążenie',
    summary: 'Komponent LQ używa przede wszystkim ACWR. Monotonia i strain są kontekstem obciążenia, ale mają inną skalę niż ACWR.',
    series: [
      { sourceKey: 'acwr_ewma', chartKey: 'acwr_ewma', label: 'ACWR EWMA', unit: 'proporcja', description: 'Relacja obciążenia ostrego do chronicznego w wersji EWMA.', color: '#0066CC', axisKind: 'ratio' },
      { sourceKey: 'acwr_rolling', chartKey: 'acwr_rolling', label: 'ACWR rolling', unit: 'proporcja', description: 'Relacja obciążenia ostrego do chronicznego w oknach kroczących.', color: '#008A4B', axisKind: 'ratio' },
      { sourceKey: 'monotony_7d', chartKey: 'monotony_7d', label: 'Monotonia 7d', unit: 'wskaźnik', description: 'Jednorodność obciążenia w ostatnich 7 dniach.', color: '#FFB000', axisKind: 'ratio' },
      { sourceKey: 'strain_7d', chartKey: 'strain_7d', label: 'Strain 7d', unit: 'jednostki obciążenia', description: 'Siedmiodniowy strain wyprowadzony wcześniej z obciążenia i monotonii.', color: '#D00000', axisKind: 'load' }
    ]
  },
  REC: {
    title: 'Regeneracja',
    tabLabel: 'Gotowość',
    summary: 'Komponent REC korzysta z gotowego readiness oraz dostępnych podskładowych readiness. Wszystkie wartości są w skali punktowej.',
    series: [
      { sourceKey: 'readiness_score', chartKey: 'readiness_score', label: 'Gotowość ogólna', unit: '0-100 pkt', description: 'Gotowy wynik readiness z wcześniejszego modułu.', color: '#008A4B', axisKind: 'score' },
      { sourceKey: 'rhr_readiness_score', chartKey: 'rhr_readiness_score', label: 'Gotowość RHR', unit: '0-100 pkt', description: 'Podskładowa readiness zależna od tętna spoczynkowego względem baseline.', color: '#D00000', axisKind: 'score' },
      { sourceKey: 'hrv_readiness_score', chartKey: 'hrv_readiness_score', label: 'Gotowość HRV', unit: '0-100 pkt', description: 'Podskładowa readiness z nocnego HRV.', color: '#7A00CC', axisKind: 'score' },
      { sourceKey: 'stress_readiness_score', chartKey: 'stress_readiness_score', label: 'Gotowość stresu', unit: '0-100 pkt', description: 'Podskładowa readiness na podstawie stresu.', color: '#FFB000', axisKind: 'score' },
    ]
  },
  CAP: {
    title: 'Pojemność treningowa',
    tabLabel: 'Aktywność',
    summary: 'Komponent CAP odnosi wykonane aktywności do wcześniejszego kontekstu obciążenia. Każda zmienna ma osobną skalę.',
    series: [
      { sourceKey: 'activity_total_duration_seconds', chartKey: 'activity_total_duration_hours', label: 'Czas aktywności', unit: 'godziny', description: 'Łączny czas aktywności w dniu, pokazany w godzinach.', color: '#0066CC', axisKind: 'hours', scale: 'seconds_to_hours' },
      { sourceKey: 'acute_ewma_7d', chartKey: 'acute_ewma_7d', label: 'Obciążenie ostre EWMA', unit: 'jednostki obciążenia', description: 'Krótkoterminowe obciążenie z poprzedniego modułu.', color: '#008A4B', axisKind: 'load' },
      { sourceKey: 'chronic_ewma_28d', chartKey: 'chronic_ewma_28d', label: 'Obciążenie chroniczne EWMA', unit: 'jednostki obciążenia', description: 'Długoterminowe obciążenie z poprzedniego modułu.', color: '#FFB000', axisKind: 'load' },
      { sourceKey: 'activity_total_distance_km', chartKey: 'activity_total_distance_km', label: 'Dystans aktywności', unit: 'km', description: 'Łączny dystans aktywności danego dnia.', color: '#A71930', axisKind: 'distance' }
    ]
  },
  VS: {
    title: 'Stabilność życiowa',
    tabLabel: 'Sygnały zdrowia',
    summary: 'Komponent VS korzysta z RHR, HRV, SpO2 podczas snu i oddechu podczas snu względem wcześniejszych baseline.',
    series: [
      { sourceKey: 'resting_hr_bpm', chartKey: 'resting_hr_bpm', label: 'Tętno spoczynkowe', unit: 'bpm', description: 'Dzienne tętno spoczynkowe z Garmina.', color: '#D00000', axisKind: 'bpm' },
      { sourceKey: 'hrv_last_night_avg_ms', chartKey: 'hrv_last_night_avg_ms', label: 'HRV z ostatniej nocy', unit: 'ms', description: 'Średnie nocne HRV z Garmina.', color: '#7A00CC', axisKind: 'ms' },
      { sourceKey: 'avg_sleep_spo2', chartKey: 'avg_sleep_spo2', label: 'Sleep SpO2', unit: '%', description: 'Średnia saturacja podczas snu, jeżeli Garmin zwraca tę konkretną wartość.', color: '#0066CC', axisKind: 'percent' },
      { sourceKey: 'avg_sleep_respiration', chartKey: 'avg_sleep_respiration', label: 'Oddech podczas snu', unit: 'oddechy/min', description: 'Średnia częstość oddechu podczas snu.', color: '#008A4B', axisKind: 'respiration' }
    ]
  }
};

function value(record: TimeSeriesRecord, series: SeriesDef): number | null {
  const raw = record[series.sourceKey];
  if (typeof raw !== 'number' || Number.isNaN(raw)) return null;
  if (series.scale === 'seconds_to_hours') return Number((raw / 3600).toFixed(2));
  return raw;
}

function hasData(records: TimeSeriesRecord[], series: SeriesDef) {
  return records.some((record) => value(record, series) !== null);
}

function valuesFor(records: TimeSeriesRecord[], series: SeriesDef) {
  return records.map((record) => value(record, series)).filter((item): item is number => item !== null);
}

function minPadding(series: SeriesDef) {
  switch (series.axisKind) {
    case 'score':
      return 5;
    case 'ratio':
      return 0.05;
    case 'percent':
      return 1;
    case 'hours':
      return 0.25;
    case 'distance':
      return 0.5;
    case 'bpm':
      return 2;
    case 'ms':
      return 5;
    case 'respiration':
      return 0.5;
    case 'load':
    default:
      return 100;
  }
}

function yDomain(series: SeriesDef, values: number[]): [number, number] {
  if (series.axisKind === 'score') return [0, 100];
  if (values.length === 0) return [0, 1];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min;
  const pad = Math.max(range * 0.16, minPadding(series));
  const floorAtZero = ['ratio', 'load', 'hours', 'distance', 'percent', 'respiration', 'ms'].includes(series.axisKind);
  const lower = floorAtZero ? Math.max(0, min - pad) : min - pad;
  const upper = series.axisKind === 'percent' ? Math.min(100, max + pad) : max + pad;
  if (lower === upper) return [Math.max(0, lower - pad), upper + pad];
  return [Number(lower.toFixed(2)), Number(upper.toFixed(2))];
}

function formatValue(input: unknown, series: SeriesDef) {
  if (input === null || input === undefined) return 'Brak danych';
  const numeric = typeof input === 'number' ? input : Number(input);
  if (Number.isNaN(numeric)) return String(input);
  switch (series.axisKind) {
    case 'score':
    case 'percent':
      return numeric.toFixed(1);
    case 'ratio':
      return numeric.toFixed(2);
    case 'load':
      return Math.round(numeric).toLocaleString('pl-PL');
    case 'hours':
    case 'distance':
    case 'respiration':
      return numeric.toFixed(2);
    case 'bpm':
    case 'ms':
    default:
      return numeric.toFixed(0);
  }
}

export function PwsComponentInputsPanel({ records }: { records: TimeSeriesRecord[] }) {
  const [selected, setSelected] = useState<ComponentId>('LQ');
  const [selectedChartKey, setSelectedChartKey] = useState<string>('acwr_ewma');
  const selectedConfig = componentInputs[selected];
  const activeSeries = selectedConfig.series.find((series) => series.chartKey === selectedChartKey) ?? selectedConfig.series[0];
  const activeValues = useMemo(() => valuesFor(records, activeSeries), [records, activeSeries]);
  const activeHasData = activeValues.length > 0;
  const chartData = useMemo(
    () => records.map((record) => ({ date: record.date, [activeSeries.chartKey]: value(record, activeSeries) })),
    [records, activeSeries]
  );
  const domain = useMemo(() => yDomain(activeSeries, activeValues), [activeSeries, activeValues]);

  function selectComponent(component: ComponentId) {
    const nextConfig = componentInputs[component];
    const firstAvailable = nextConfig.series.find((series) => hasData(records, series)) ?? nextConfig.series[0];
    setSelected(component);
    setSelectedChartKey(firstAvailable.chartKey);
  }

  return (
    <section className="card wide component-inputs-panel" aria-label="Zmienne wejściowe komponentów PWS">
      <div className="card-heading">
        <div>
          <p className="eyebrow">Wejścia PWS</p>
          <h2>Zmienne źródłowe komponentów PWS</h2>
        </div>
      </div>
      <div className="component-selector" role="tablist" aria-label="Komponenty PWS">
        {(Object.keys(componentInputs) as ComponentId[]).map((component) => (
          <button
            key={component}
            type="button"
            className={selected === component ? 'active' : ''}
            onClick={() => selectComponent(component)}
          >
            <strong>{component}</strong>
            <span>{componentInputs[component].tabLabel}</span>
          </button>
        ))}
      </div>
      <div className="component-input-detail">
        <div>
          <h3>{selected}: {selectedConfig.title}</h3>
          <p className="muted">{selectedConfig.summary}</p>
          <div className="input-variable-list" aria-label="Lista zmiennych komponentu">
            {selectedConfig.series.map((series) => {
              const available = hasData(records, series);
              const isActive = activeSeries.chartKey === series.chartKey;
              return (
                <button
                  key={series.chartKey}
                  type="button"
                  className={`input-variable-item${isActive ? ' active' : ''}${available ? '' : ' missing'}`}
                  aria-pressed={isActive}
                  onClick={() => setSelectedChartKey(series.chartKey)}
                >
                  <span className="variable-name">{series.label}</span>
                  <span className="variable-meta">{series.unit} - {available ? 'dostępne' : 'brak danych'}</span>
                  <span className="variable-source">{String(series.sourceKey)}</span>
                </button>
              );
            })}
          </div>
        </div>
        <div className="chart-wrap compact-chart variable-chart-card">
          <div className="variable-chart-heading">
            <div>
              <h3>Trend: {activeSeries.label}</h3>
              <p className="muted">{activeSeries.description}</p>
            </div>
            <span>{activeSeries.unit}</span>
          </div>
          {!activeHasData ? (
            <p className="notice">Brak danych dla tej zmiennej w aktualnym payloadzie.</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData} margin={{ top: 12, right: 20, left: 8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" minTickGap={20} />
                <YAxis domain={domain} width={72} tickFormatter={(tick) => formatValue(tick, activeSeries)} />
                <Tooltip formatter={(tooltipValue) => [`${formatValue(tooltipValue, activeSeries)} ${activeSeries.unit}`, activeSeries.label]} labelFormatter={(label) => `Data: ${label}`} />
                <Line key={activeSeries.chartKey} type="monotone" dataKey={activeSeries.chartKey} name={activeSeries.label} stroke={activeSeries.color} strokeWidth={2.5} connectNulls={false} dot={false} activeDot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </section>
  );
}
