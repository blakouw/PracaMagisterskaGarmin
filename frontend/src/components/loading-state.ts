import { Component } from '@angular/core';

@Component({
  selector: 'app-loading-state',
  host: { class: 'dashboard-section' },
  template: `
    <main class="shell">
      <section class="state-panel" aria-live="polite">
        <div class="spinner"></div>
        <h1>Ładowanie lokalnego dashboardu</h1>
        <p>Odczyt aktualnego snapshotu przez lokalne API tylko do odczytu.</p>
      </section>
    </main>
  `
})
export class LoadingState {}
