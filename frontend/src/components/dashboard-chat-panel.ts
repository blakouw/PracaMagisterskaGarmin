import { Component, inject, input, signal, type OnInit } from '@angular/core';
import { DashboardApi } from '../api/dashboardApi';
import type { DashboardChatMessage, DashboardCurrentState, SnapshotStatus } from '../api/dashboardTypes';
import { formatScore } from '../utils/formatters';

@Component({
  selector: 'app-dashboard-chat-panel',
  host: { class: 'dashboard-section' },
  templateUrl: './dashboard-chat-panel.html'
})
export class DashboardChatPanel implements OnInit {
  private readonly api = inject(DashboardApi);
  readonly current = input.required<DashboardCurrentState>();
  readonly snapshotStatus = input<SnapshotStatus | null>(null);
  protected readonly messages = signal<DashboardChatMessage[]>([]);
  protected readonly draft = signal('');
  protected readonly pending = signal(false);
  protected readonly error = signal<string | null>(null);

  ngOnInit(): void {
    const state = this.current();
    const snapshot = this.snapshotStatus()?.snapshot_id ?? 'current';
    const score = formatScore(state.primary_pws.score);
    const status = state.optional_assisted_pws.available ? 'dostępny' : state.optional_assisted_pws.status;
    this.messages.set([{
      role: 'assistant',
      content: `Jestem gotowy do lokalnej rozmowy LLM o snapshocie ${snapshot} z dnia ${state.date}. Deterministyczny PWS to ${score}, a status wariantu asystowanego to ${status}.`
    }]);
  }

  protected async send(event: Event): Promise<void> {
    event.preventDefault();
    const question = this.draft().trim();
    if (!question || this.pending()) return;

    const history = this.messages().slice(-8);
    this.messages.update(items => [...items, { role: 'user', content: question }]);
    this.draft.set('');
    this.error.set(null);
    this.pending.set(true);
    try {
      const response = await this.api.sendDashboardChatMessage({ message: question, history });
      this.messages.update(items => [...items, { role: 'assistant', content: response.answer }]);
    } catch {
      this.error.set('Lokalny czat LLM jest niedostępny. Sprawdź, czy API i Ollama działają lokalnie.');
      this.messages.update(items => [...items, {
        role: 'assistant',
        content: 'Nie udało mi się uzyskać lokalnej odpowiedzi LLM dla tej wiadomości.'
      }]);
    } finally {
      this.pending.set(false);
    }
  }
}
