import { Component, input } from '@angular/core';
import type { LoadMetricsState } from '../api/dashboardTypes';
import { formatNumber } from '../utils/formatters';

@Component({
  selector: 'app-load-metrics-panel',
  host: { class: 'dashboard-section' },
  template: `
    <section class="card">
      <p class="eyebrow">Kontekst analityczny</p>
      <h2>Metryki obciążenia</h2>
      <div class="metric-grid">
        @for (field of fields; track field[0]) {
          <div class="metric">
            <span>{{ field[1] }}</span>
            <strong>{{ formatNumber(metrics()[field[0]], 2) }}</strong>
          </div>
        }
      </div>
    </section>
  `
})
export class LoadMetricsPanel {
  readonly metrics = input.required<LoadMetricsState>();
  protected readonly formatNumber = formatNumber;
  protected readonly fields = [
    ['acwr_ewma', 'ACWR EWMA'],
    ['acwr_rolling', 'ACWR rolling'],
    ['acute_ewma_7d', 'Obciążenie ostre EWMA 7d'],
    ['chronic_ewma_28d', 'Obciążenie chroniczne EWMA 28d'],
    ['monotony_7d', 'Monotonia 7d'],
    ['strain_7d', 'Strain 7d']
  ] as const;
}
