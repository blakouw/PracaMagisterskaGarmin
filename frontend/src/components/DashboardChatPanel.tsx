import { useMemo, useState } from 'react';
import { sendDashboardChatMessage } from '../api/dashboardApi';
import type { DashboardChatMessage, DashboardCurrentState, DashboardDisclosures, DashboardQualityAndCoverage, SnapshotStatus } from '../api/dashboardTypes';
import { formatScore } from '../utils/formatters';

interface Props {
  current: DashboardCurrentState;
  snapshotStatus: SnapshotStatus | null;
  quality: DashboardQualityAndCoverage | null;
  disclosures: DashboardDisclosures | null;
}

interface Message {
  role: 'user' | 'assistant';
  text: string;
}

function toApiHistory(messages: Message[]): DashboardChatMessage[] {
  return messages.slice(-8).map((message) => ({ role: message.role, content: message.text }));
}

export function DashboardChatPanel({ current, snapshotStatus, quality: _quality, disclosures: _disclosures }: Props) {
  const initial = useMemo<Message>(() => ({
    role: 'assistant',
    text: `Jestem gotowy do lokalnej rozmowy LLM o snapshocie ${snapshotStatus?.snapshot_id ?? 'current'} z dnia ${current.date}. Deterministyczny PWS to ${formatScore(current.primary_pws.score)}, a status wariantu asystowanego to ${current.optional_assisted_pws.available ? 'dostępny' : current.optional_assisted_pws.status}.`
  }), [current, snapshotStatus]);
  const [messages, setMessages] = useState<Message[]>([initial]);
  const [draft, setDraft] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send() {
    const question = draft.trim();
    if (!question || pending) return;
    const nextMessages = [...messages, { role: 'user' as const, text: question }];
    setMessages(nextMessages);
    setDraft('');
    setError(null);
    setPending(true);
    try {
      const response = await sendDashboardChatMessage({ message: question, history: toApiHistory(messages) });
      setMessages((items) => [...items, { role: 'assistant', text: response.answer }]);
    } catch {
      setError('Lokalny czat LLM jest niedostępny. Sprawdź, czy API i Ollama działają lokalnie.');
      setMessages((items) => [...items, { role: 'assistant', text: 'Nie udało mi się uzyskać lokalnej odpowiedzi LLM dla tej wiadomości.' }]);
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="card wide chat-panel" aria-label="Panel czatu dashboardu">
      <div className="card-heading">
        <div>
          <h2>Czat o snapshocie</h2>
        </div>
      </div>
      <div className="chat-log" aria-live="polite">
        {messages.map((message, index) => (
          <div key={`${message.role}-${index}`} className={`chat-message ${message.role}`}>
            <span>{message.role === 'assistant' ? 'Asystent' : 'Ty'}</span>
            <p>{message.text}</p>
          </div>
        ))}
      </div>
      {error ? <p className="notice error-banner">{error}</p> : null}
      <div className="chat-input-row">
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') void send();
          }}
          placeholder="Wpisz pytanie o dashboard"
          aria-label="Pytanie o dashboard"
          disabled={pending}
        />
        <button type="button" onClick={() => void send()} disabled={pending}>{pending ? 'Wysyłanie' : 'Wyślij'}</button>
      </div>
    </section>
  );
}
