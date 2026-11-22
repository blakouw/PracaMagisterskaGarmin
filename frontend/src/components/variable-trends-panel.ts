import { Component, computed, input, signal } from '@angular/core';
import { BaseChartDirective } from 'ng2-charts';
import type { TimeSeriesRecord } from '../api/dashboardTypes';
import { weightChartDomain } from '../utils/chartScale';
import { hasSeries, lineData, lineOptions, type LineSeries } from '../utils/lineChart';

const dailySeries: LineSeries[] = [
  { sourceKey: 'resting_hr_bpm', label: 'Tętno spoczynkowe', color: '#D00000' },
  { sourceKey: 'sleep_seconds', label: 'Sen w godzinach', color: '#0066CC', scale: 'seconds_to_hours' },
  { sourceKey: 'hrv_last_night_avg_ms', label: 'HRV', color: '#7A00CC' },
  { sourceKey: 'avg_stress', label: 'Stres', color: '#FFB000' },
  { sourceKey: 'activity_duration_weighted_average_hr_bpm', label: 'Średnie tętno aktywności', color: '#008A4B' },
  { sourceKey: 'activity_maximum_hr_bpm', label: 'Maksymalne tętno aktywności', color: '#A71930' },
  { sourceKey: 'avg_sleep_spo2', label: 'Sleep SpO2', color: '#00A0C6' }
];

const deterministicWeightSeries: LineSeries[] = [
  { sourceKey: 'weight_lq', label: 'Waga LQ - Load Quality', color: '#0066CC' },
  { sourceKey: 'weight_rec', label: 'Waga REC - Recovery', color: '#008A4B' },
  { sourceKey: 'weight_cap', label: 'Waga CAP - Capacity', color: '#FFB000' },
  { sourceKey: 'weight_vs', label: 'Waga VS - Vital Stability', color: '#D00000' }
];

const localLlmWeightSeries: LineSeries[] = [
  { sourceKey: 'local_llm_weight_lq', label: 'Waga LQ - Load Quality', color: '#0066CC' },
  { sourceKey: 'local_llm_weight_rec', label: 'Waga REC - Recovery', color: '#008A4B' },
  { sourceKey: 'local_llm_weight_cap', label: 'Waga CAP - Capacity', color: '#FFB000' },
  { sourceKey: 'local_llm_weight_vs', label: 'Waga VS - Vital Stability', color: '#D00000' }
];

const openAiWeightSeries: LineSeries[] = [
  { sourceKey: 'openai_weight_lq', label: 'Waga LQ - Load Quality', color: '#0066CC' },
  { sourceKey: 'openai_weight_rec', label: 'Waga REC - Recovery', color: '#008A4B' },
  { sourceKey: 'openai_weight_cap', label: 'Waga CAP - Capacity', color: '#FFB000' },
  { sourceKey: 'openai_weight_vs', label: 'Waga VS - Vital Stability', color: '#D00000' }
];

const weightVariants = [
  {
    title: 'Wagi komponentów PWS w czasie — wariant deterministyczny',
    label: 'Wagi deterministyczne PWS w czasie',
    series: deterministicWeightSeries
  },
  {
    title: 'Wagi komponentów PWS w czasie — lokalny LLM',
    label: 'Wagi lokalnego LLM w czasie',
    series: localLlmWeightSeries
  },
  {
    title: 'Wagi komponentów PWS w czasie — OpenAI',
    label: 'Wagi OpenAI w czasie',
    series: openAiWeightSeries
  }
];

@Component({
  selector: 'app-variable-trends-panel',
  host: { class: 'dashboard-section' },
  imports: [BaseChartDirective],
  templateUrl: './variable-trends-panel.html'
})
export class VariableTrendsPanel {
  readonly records = input.required<TimeSeriesRecord[]>();
  protected readonly visible = signal(new Set<keyof TimeSeriesRecord>(['resting_hr_bpm', 'sleep_seconds', 'hrv_last_night_avg_ms']));
  protected readonly availableDaily = computed(() => dailySeries.filter(series => hasSeries(this.records(), series)));
  protected readonly dailyData = computed(() => {
    const visible = this.availableDaily().filter(series => this.visible().has(series.sourceKey));
    return lineData(this.records(), visible);
  });
  protected readonly dailyOptions = lineOptions({ beginAtZero: true, valueFormat: String });
  protected readonly weights = computed(() => {
    const records = this.records();
    return weightVariants.map(variant => {
      const series = variant.series.filter(item => hasSeries(records, item));
      return {
        title: variant.title,
        label: variant.label,
        data: series.length ? lineData(records, series) : null,
        options: lineOptions({
          domain: weightChartDomain(records, series.map(item => item.sourceKey)),
          tickCount: 6,
          tickFormat: value => Math.round(value * 100) + '%',
          valueFormat: value => (value * 100).toFixed(1).replace('.', ',') + '%'
        })
      };
    });
  });

  protected toggleSeries(key: keyof TimeSeriesRecord, enabled: boolean): void {
    const next = new Set(this.visible());
    if (enabled) next.add(key);
    else next.delete(key);
    this.visible.set(next);
  }
}
