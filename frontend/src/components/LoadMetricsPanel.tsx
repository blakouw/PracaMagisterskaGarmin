import type { LoadMetricsState } from '../api/dashboardTypes';
import { formatNumber } from '../utils/formatters';

interface Props {
  metrics: LoadMetricsState;
}

const fields: Array<[keyof LoadMetricsState, string]> = [
  ['acwr_ewma', 'ACWR EWMA'],
  ['acwr_rolling', 'ACWR rolling'],
  ['acute_ewma_7d', 'Obciążenie ostre EWMA 7d'],
  ['chronic_ewma_28d', 'Obciążenie chroniczne EWMA 28d'],
  ['monotony_7d', 'Monotonia 7d'],
  ['strain_7d', 'Strain 7d']
];

export function LoadMetricsPanel({ metrics }: Props) {
  return (
    <section className="card">
      <p className="eyebrow">Kontekst analityczny</p>
      <h2>Metryki obciążenia</h2>
      <div className="metric-grid">
        {fields.map(([key, label]) => (
          <div className="metric" key={key}>
            <span>{label}</span>
            <strong>{formatNumber(metrics[key] as number | null | undefined, 2)}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
