import { Component, computed, input, signal } from '@angular/core';
import { BaseChartDirective } from 'ng2-charts';
import type { TimeSeriesRecord } from '../api/dashboardTypes';
import { hasSeries, lineData, lineOptions, seriesValue, type LineSeries } from '../utils/lineChart';

type ComponentId = 'LQ' | 'REC' | 'CAP' | 'VS';
type AxisKind = 'score' | 'ratio' | 'load' | 'hours' | 'distance' | 'bpm' | 'ms' | 'percent' | 'respiration';

interface SeriesDef extends LineSeries {
  chartKey: string;
  unit: string;
  description: string;
  axisKind: AxisKind;
}

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

@Component({
  selector: 'app-pws-component-inputs-panel',
  host: { class: 'dashboard-section' },
  imports: [BaseChartDirective],
  templateUrl: './pws-component-inputs-panel.html'
})
export class PwsComponentInputsPanel {
  readonly records = input.required<TimeSeriesRecord[]>();
  protected readonly components = componentInputs;
  protected readonly keys = Object.keys(componentInputs) as ComponentId[];
  protected readonly selected = signal<ComponentId>('LQ');
  protected readonly selectedChartKey = signal('acwr_ewma');
  protected readonly selectedConfig = computed(() => componentInputs[this.selected()]);
  protected readonly seriesList = computed(() => {
    const records = this.records();
    return this.selectedConfig().series.map(series => ({ series, available: hasSeries(records, series) }));
  });
  protected readonly active = computed(() => {
    const list = this.seriesList();
    return list.find(item => item.series.chartKey === this.selectedChartKey()) ?? list[0];
  });
  protected readonly chartData = computed(() => lineData(this.records(), [this.active().series]));
  protected readonly chartOptions = computed(() => {
    const { series } = this.active();
    const values = this.records().map(record => seriesValue(record, series)).filter((value): value is number => value !== null);
    return lineOptions({
      domain: yDomain(series, values),
      legend: false,
      datePrefix: true,
      tickFormat: value => formatValue(value, series),
      valueFormat: value => formatValue(value, series) + ' ' + series.unit
    });
  });

  protected selectComponent(component: ComponentId): void {
    const series = componentInputs[component].series;
    const firstAvailable = series.find(item => hasSeries(this.records(), item)) ?? series[0];
    this.selected.set(component);
    this.selectedChartKey.set(firstAvailable.chartKey);
  }
}
