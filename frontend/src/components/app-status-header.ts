import { Component } from '@angular/core';

@Component({
  selector: 'app-status-header',
  host: { class: 'dashboard-section' },
  template: `
    <header class="app-header">
      <div>
        <p class="eyebrow">Lokalny widok tylko do odczytu</p>
        <h1>Panel Personal Wellness</h1>
      </div>
    </header>
  `
})
export class AppStatusHeader {}
