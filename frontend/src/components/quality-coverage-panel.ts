import { Component, computed, input } from '@angular/core';
import type { CoverageState, DashboardQualityAndCoverage } from '../api/dashboardTypes';
import { formatPercent } from '../utils/formatters';

@Component({
  selector: 'app-quality-coverage-panel',
  host: { class: 'dashboard-section' },
  template: `
    @let availability = quality()?.presentation_availability;
    @let tiers = quality()?.coverage_tiers;
    <section class="card">
      <p class="eyebrow">Jakość danych</p>
      <h2>Jakość i pokrycie</h2>
      @if (error(); as message) {
        <p class="notice error-text">{{ message }}</p>
      }
      @if (disclosuresError(); as message) {
        <p class="notice error-text">{{ message }}</p>
      }
      <div class="metric-grid">
        <div class="metric"><span>Dni z policzonym PWS</span><strong>{{ availability?.primary_pws_computed_count ?? 'Brak danych' }}</strong></div>
        <div class="metric"><span>Dni bez PWS</span><strong>{{ availability?.primary_pws_unavailable_count ?? 'Brak danych' }}</strong></div>
        <div class="metric"><span>Częściowe pokrycie</span><strong>{{ tiers?.partial_eligible ?? 'Brak danych' }}</strong></div>
        <div class="metric"><span>Niewystarczające dane</span><strong>{{ tiers?.insufficient ?? 'Brak danych' }}</strong></div>
        <div class="metric"><span>Aktualne pokrycie PWS</span><strong>{{ formatPercent(coverage().pws_coverage_ratio) }}</strong></div>
      </div>
      <p class="muted">Brakujące komponenty PWS: {{ coverage().missing_pws_components?.join(', ') || 'Brak' }}</p>
      <p class="muted">Brakujące komponenty gotowości: {{ coverage().missing_readiness_components?.join(', ') || 'Brak' }}</p>
      @if (componentCoverage().length) {
        <div class="component-availability">
          @for (entry of componentCoverage(); track entry[0]) {
            <span>{{ entry[0] }}: {{ formatPercent(entry[1].coverage_ratio) }}</span>
          }
        </div>
      }
    </section>
  `
})
export class QualityCoveragePanel {
  readonly coverage = input.required<CoverageState>();
  readonly quality = input<DashboardQualityAndCoverage | null>(null);
  readonly error = input<string>();
  readonly disclosuresError = input<string>();
  protected readonly formatPercent = formatPercent;
  protected readonly componentCoverage = computed(() => Object.entries(this.quality()?.component_availability ?? {}));
}
