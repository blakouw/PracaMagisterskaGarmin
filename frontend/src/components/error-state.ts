import { Component, input } from '@angular/core';

@Component({
  selector: 'app-error-state',
  host: { class: 'dashboard-section' },
  template: `
    <main class="shell">
      <section class="state-panel error">
        @if (kind() === 'api') {
          <h1>Lokalne API dashboardu jest niedostępne</h1>
          <p>Uruchom lokalne API tylko do odczytu i odśwież stronę.</p>
        } @else {
          <h1>Brak poprawnego opublikowanego snapshotu dashboardu</h1>
          <p>API działa, ale nie ma aktualnie poprawnego opublikowanego snapshotu.</p>
        }
        @if (detail(); as description) {
          <p class="muted">{{ description }}</p>
        }
      </section>
    </main>
  `
})
export class ErrorState {
  readonly kind = input.required<'api' | 'snapshot'>();
  readonly detail = input<string>();
}
