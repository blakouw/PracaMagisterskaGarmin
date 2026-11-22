import { Component, computed, input, linkedSignal, output, signal } from '@angular/core';
import type { Chart, Plugin } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';
import type { OptionalAssistedPws, PrimaryPws, TimeSeriesRecord } from '../api/dashboardTypes';
import { scoreChartDomain, symmetricDeltaDomain } from '../utils/chartScale';
import { formatDate, formatScore } from '../utils/formatters';
import { lineData, lineOptions, type LineSeries } from '../utils/lineChart';

const rangeOptions = [7, 30, 90, 'all'] as const;
export type DashboardRange = typeof rangeOptions[number];

const scores: LineSeries[] = [
  { sourceKey: 'pws_deterministic', label: 'Deterministyczny PWS', color: '#FFFFFF', width: 3 },
  { sourceKey: 'optional_assisted_pws', label: 'Lokalny LLM', color: '#00693C', width: 3, dash: [8, 4] },
  { sourceKey: 'external_assisted_pws', label: 'OpenAI', color: '#A71930', width: 3, dash: [3, 3] }
];
const deltas: LineSeries[] = [
  { sourceKey: 'optional_assisted_delta_from_deterministic', label: 'Lokalny LLM vs PWS', color: '#00693C', width: 3, linear: true },
  { sourceKey: 'external_assisted_delta_from_deterministic', label: 'OpenAI vs PWS', color: '#A71930', width: 3, linear: true }
];

interface ScoreLayout {
  ticks: { date: string; position: number }[];
  firstPosition: number;
  lastPosition: number;
  plotTop: number;
  plotHeight: number;
  ticksTop: number;
}

function signed(value: number): string {
  return (value > 0 ? '+' : '') + value.toLocaleString('pl-PL', { maximumFractionDigits: 2 });
}

@Component({
  selector: 'app-pws-model-comparison-panel',
  host: { class: 'dashboard-section' },
  imports: [BaseChartDirective],
  templateUrl: './pws-model-comparison-panel.html'
})
export class PwsModelComparisonPanel {
  readonly records = input.required<TimeSeriesRecord[]>();
  readonly primary = input.required<PrimaryPws>();
  readonly localAssisted = input.required<OptionalAssistedPws>();
  readonly externalAssisted = input<OptionalAssistedPws>();
  readonly range = input.required<DashboardRange>();
  readonly error = input<string>();
  readonly rangeChange = output<DashboardRange>();
  protected readonly options = rangeOptions;
  protected readonly formatDate = formatDate;
  protected readonly formatScore = formatScore;

  private readonly selectedDate = linkedSignal<TimeSeriesRecord[], string | null>({
    source: this.records,
    computation: (records, previous) => {
      const date = previous?.value;
      return date && records.some(record => record.date === date) ? date : (records.at(-1)?.date ?? null);
    }
  });
  protected readonly layout = signal<ScoreLayout | null>(null);
  protected readonly selectedRecord = computed(() => {
    const date = this.selectedDate();
    return this.records().find(record => record.date === date) ?? this.records().at(-1) ?? null;
  });
  protected readonly summary = computed(() => {
    const record = this.selectedRecord();
    const local = this.localAssisted();
    const external = this.externalAssisted();
    return {
      primary: record ? record.pws_deterministic : this.primary().score,
      local: record ? record.optional_assisted_pws : (local.available ? local.score : null),
      external: record ? record.external_assisted_pws : (external?.available ? external.score : null),
      localDelta: record ? record.optional_assisted_delta_from_deterministic : local.delta_from_deterministic,
      externalDelta: record ? record.external_assisted_delta_from_deterministic : external?.delta_from_deterministic,
      localDays: this.records().filter(row => row.optional_assisted_pws != null).length,
      externalDays: this.records().filter(row => row.external_assisted_pws != null).length,
      localLabel: local.model ? 'Lokalny LLM · ' + local.model : 'Lokalny LLM',
      externalLabel: external?.model ? 'OpenAI · ' + external.model : 'Model zewnętrzny · OpenAI'
    };
  });

  protected readonly scoreData = computed(() => lineData(this.records(), scores));
  protected readonly deltaData = computed(() => lineData(this.records(), deltas));
  protected readonly scoreOptions = computed(() => lineOptions({
    domain: scoreChartDomain(this.records(), scores.map(series => series.sourceKey)),
    tickCount: 7,
    dateTickButtons: true,
    onDateSelect: date => this.selectDate(date)
  }));
  protected readonly deltaOptions = computed(() => lineOptions({
    domain: symmetricDeltaDomain(this.records(), deltas.map(series => series.sourceKey)),
    zeroLine: true,
    tickFormat: signed,
    valueFormat: value => this.formatDelta(value)
  }));
  protected readonly scorePlugins: Plugin<'line'>[] = [{
    id: 'dashboard-date-axis',
    afterLayout: chart => this.updateLayout(chart)
  }];

  protected readonly marker = computed(() => {
    const layout = this.layout();
    const index = this.records().findIndex(record => record.date === this.selectedRecord()?.date);
    if (!layout || index < 0) return null;
    const progress = index / Math.max(1, this.records().length - 1);
    return layout.firstPosition + (layout.lastPosition - layout.firstPosition) * progress;
  });

  protected selectDate(date: string): void {
    this.selectedDate.set(date);
  }

  protected formatDelta(value: number | null | undefined): string {
    return value == null ? 'Brak różnicy' : signed(value) + ' pkt';
  }

  private updateLayout(chart: Chart<'line'>): void {
    const axis = chart.scales['x'];
    const lastIndex = (chart.data.labels?.length ?? 0) - 1;
    if (!axis || chart.width === 0 || lastIndex < 0) {
      queueMicrotask(() => this.layout.set(null));
      return;
    }
    const position = (pixel: number) => pixel * 100 / chart.width;
    const layout: ScoreLayout = {
      ticks: axis.ticks.map((tick, index) => ({
        date: axis.getLabelForValue(tick.value),
        position: position(axis.getPixelForTick(index))
      })),
      firstPosition: position(axis.getPixelForValue(0)),
      lastPosition: position(axis.getPixelForValue(lastIndex)),
      plotTop: chart.chartArea.top,
      plotHeight: chart.chartArea.bottom - chart.chartArea.top,
      ticksTop: axis.top + 7
    };
    queueMicrotask(() => this.layout.set(layout));
  }
}
