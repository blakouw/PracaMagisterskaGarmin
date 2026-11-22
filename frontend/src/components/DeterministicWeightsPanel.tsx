import type { PwsWeightsState } from '../api/dashboardTypes';
import { formatNumber } from '../utils/formatters';
import { formatPwsComponentLabel } from '../utils/pwsLabels';

interface Props {
  weights: PwsWeightsState;
}

const weightKeys = ['LQ', 'REC', 'CAP', 'VS'];

export function DeterministicWeightsPanel({ weights }: Props) {
  const effective = weights.deterministic_effective_weights;
  return (
    <section className="card">
      <h2>Wagi deterministyczne</h2>
      <div className="metric-grid">
        {weightKeys.map((key) => (
          <div className="metric" key={key}>
            <span>{formatPwsComponentLabel(key)}</span>
            <strong>{formatNumber(effective?.[key] ?? null, 2)}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
