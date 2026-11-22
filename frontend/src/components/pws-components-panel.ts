import { Component, input } from '@angular/core';
import type { PwsComponentsState } from '../api/dashboardTypes';
import { formatScore } from '../utils/formatters';

const names: Record<string, string> = {
  'Load Quality': 'Jakość obciążenia',
  Recovery: 'Regeneracja',
  Capacity: 'Pojemność treningowa',
  'Vital Stability': 'Stabilność życiowa'
};

@Component({
  selector: 'app-pws-components-panel',
  host: { class: 'dashboard-section' },
  template: `
    <section class="card">
      <p class="eyebrow">Komponenty PWS</p>
      <h2>LQ, REC, CAP, VS</h2>
      <div class="component-list">
        @for (key of keys; track key) {
          @let item = components()[key];
          @let score = item?.score ?? null;
          <div class="component-row">
            <div>
              <strong>{{ key }}</strong>
              <span>{{ componentName(item?.name) }}</span>
            </div>
            <div class="bar-wrap" [attr.aria-label]="key + ' wynik ' + formatScore(score)">
              <div class="bar" [style.width.%]="barWidth(score)"></div>
            </div>
            <span>{{ formatScore(score) }}</span>
            <small>{{ item?.status ?? 'Brak danych' }}</small>
          </div>
        }
      </div>
    </section>
  `
})
export class PwsComponentsPanel {
  readonly components = input.required<PwsComponentsState>();
  protected readonly keys = ['LQ', 'REC', 'CAP', 'VS'] as const;
  protected readonly formatScore = formatScore;

  protected componentName(name: string | null | undefined): string {
    return name ? (names[name] ?? name) : 'Brak danych';
  }

  protected barWidth(score: number | null): number {
    return Math.max(0, Math.min(100, score ?? 0));
  }
}
