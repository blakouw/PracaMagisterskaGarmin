import type { PrimaryPws } from '../api/dashboardTypes';
import { isInsufficientCoverage, isPartialCoverage } from '../utils/coverage';
import { formatPercent, formatScore, titleCase } from '../utils/formatters';

interface Props {
  primary: PrimaryPws;
}

export function PrimaryPwsCard({ primary }: Props) {
  const scoreAvailable = primary.computed && primary.score !== null && primary.score !== undefined;
  const partial = isPartialCoverage(primary.coverage_tier);
  const insufficient = isInsufficientCoverage(primary.coverage_tier) || !scoreAvailable;

  return (
    <section className="card primary-card" aria-label="Główny deterministyczny PWS">
      <div className="card-heading">
        <div>
          <h2>Deterministyczny PWS</h2>
        </div>
      </div>
      <div className={scoreAvailable ? 'score-value' : 'score-value missing'}>{formatScore(primary.score)}</div>
      <p className="score-label">{scoreAvailable ? titleCase(primary.label) : 'Niewystarczające pokrycie komponentów'}</p>
      <p className="muted">Pokrycie: {formatPercent(primary.coverage_ratio)}</p>
      {partial ? <p className="notice">Wynik policzono z dopuszczalnego, ale niepełnego zestawu komponentów.</p> : null}
      {!scoreAvailable ? (
        <div className="notice">
          <strong>Brak wyniku</strong>
          <p>Dostępne komponenty: {(primary.available_components ?? []).join(', ') || 'Brak danych'}</p>
          <p>Brakujące komponenty: {(primary.missing_components ?? []).join(', ') || 'Brak danych'}</p>
        </div>
      ) : null}
    </section>
  );
}
