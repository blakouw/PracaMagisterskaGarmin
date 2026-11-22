import type { PwsComponentsState } from '../api/dashboardTypes';
import { formatScore } from '../utils/formatters';

interface Props {
  components: PwsComponentsState;
}

const keys = ['LQ', 'REC', 'CAP', 'VS'] as const;
const names: Record<string, string> = {
  'Load Quality': 'Jakość obciążenia',
  Recovery: 'Regeneracja',
  Capacity: 'Pojemność treningowa',
  'Vital Stability': 'Stabilność życiowa'
};

export function PwsComponentsPanel({ components }: Props) {
  return (
    <section className="card">
      <p className="eyebrow">Komponenty PWS</p>
      <h2>LQ, REC, CAP, VS</h2>
      <div className="component-list">
        {keys.map((key) => {
          const component = components[key];
          const score = component?.score ?? null;
          return (
            <div className="component-row" key={key}>
              <div>
                <strong>{key}</strong>
                <span>{names[component?.name ?? ''] ?? component?.name ?? 'Brak danych'}</span>
              </div>
              <div className="bar-wrap" aria-label={`${key} wynik ${formatScore(score)}`}>
                <div className="bar" style={{ width: score === null ? '0%' : `${Math.max(0, Math.min(100, score))}%` }} />
              </div>
              <span>{formatScore(score)}</span>
              <small>{component?.status ?? 'Brak danych'}</small>
            </div>
          );
        })}
      </div>
    </section>
  );
}
