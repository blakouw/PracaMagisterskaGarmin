import { Component, computed, input } from '@angular/core';
import type { PrimaryPws } from '../api/dashboardTypes';
import { isPartialCoverage } from '../utils/coverage';
import { formatPercent, formatScore, titleCase } from '../utils/formatters';

@Component({
  selector: 'app-primary-pws-card',
  host: { class: 'dashboard-section' },
  template: `
    @let data = primary();
    <section class="card primary-card" aria-label="Główny deterministyczny PWS">
      <div class="card-heading">
        <div><h2>Deterministyczny PWS</h2></div>
      </div>
      <div class="score-value" [class.missing]="!scoreAvailable()">{{ formatScore(data.score) }}</div>
      <p class="score-label">{{ scoreAvailable() ? titleCase(data.label) : 'Niewystarczające pokrycie komponentów' }}</p>
      <p class="muted">Pokrycie: {{ formatPercent(data.coverage_ratio) }}</p>
      @if (isPartialCoverage(data.coverage_tier)) {
        <p class="notice">Wynik policzono z dopuszczalnego, ale niepełnego zestawu komponentów.</p>
      }
      @if (!scoreAvailable()) {
        <div class="notice">
          <strong>Brak wyniku</strong>
          <p>Dostępne komponenty: {{ data.available_components?.join(', ') || 'Brak danych' }}</p>
          <p>Brakujące komponenty: {{ data.missing_components?.join(', ') || 'Brak danych' }}</p>
        </div>
      }
    </section>
  `
})
export class PrimaryPwsCard {
  readonly primary = input.required<PrimaryPws>();
  protected readonly formatScore = formatScore;
  protected readonly formatPercent = formatPercent;
  protected readonly titleCase = titleCase;
  protected readonly isPartialCoverage = isPartialCoverage;
  protected readonly scoreAvailable = computed(() => {
    const { computed, score } = this.primary();
    return computed && score !== null && score !== undefined;
  });
}
