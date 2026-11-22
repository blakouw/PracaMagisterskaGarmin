import { Component, input } from '@angular/core';
import type { PwsWeightsState } from '../api/dashboardTypes';
import { formatNumber } from '../utils/formatters';
import { formatPwsComponentLabel } from '../utils/pwsLabels';

@Component({
  selector: 'app-deterministic-weights-panel',
  host: { class: 'dashboard-section' },
  template: `
    <section class="card">
      <h2>Wagi deterministyczne</h2>
      <div class="metric-grid">
        @for (key of keys; track key) {
          <div class="metric">
            <span>{{ formatPwsComponentLabel(key) }}</span>
            <strong>{{ formatNumber(weights().deterministic_effective_weights?.[key], 2) }}</strong>
          </div>
        }
      </div>
    </section>
  `
})
export class DeterministicWeightsPanel {
  readonly weights = input.required<PwsWeightsState>();
  protected readonly keys = ['LQ', 'REC', 'CAP', 'VS'];
  protected readonly formatNumber = formatNumber;
  protected readonly formatPwsComponentLabel = formatPwsComponentLabel;
}
