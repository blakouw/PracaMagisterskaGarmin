import type { CoverageState, DashboardQualityAndCoverage } from '../api/dashboardTypes';
import { formatPercent } from '../utils/formatters';

interface Props {
  coverage: CoverageState;
  quality: DashboardQualityAndCoverage | null;
  error?: string | null;
}

export function QualityCoveragePanel({ coverage, quality, error }: Props) {
  const availability = quality?.presentation_availability;
  const tiers = quality?.coverage_tiers;
  return (
    <section className="card">
      <p className="eyebrow">Jakość danych</p>
      <h2>Jakość i pokrycie</h2>
      {error ? <p className="notice error-text">{error}</p> : null}
      <div className="metric-grid">
        <div className="metric"><span>Dni z policzonym PWS</span><strong>{availability?.primary_pws_computed_count ?? 'Brak danych'}</strong></div>
        <div className="metric"><span>Dni bez PWS</span><strong>{availability?.primary_pws_unavailable_count ?? 'Brak danych'}</strong></div>
        <div className="metric"><span>Częściowe pokrycie</span><strong>{tiers?.partial_eligible ?? 'Brak danych'}</strong></div>
        <div className="metric"><span>Niewystarczające dane</span><strong>{tiers?.insufficient ?? 'Brak danych'}</strong></div>
        <div className="metric"><span>Aktualne pokrycie PWS</span><strong>{formatPercent(coverage.pws_coverage_ratio)}</strong></div>
      </div>
      <p className="muted">Brakujące komponenty PWS: {(coverage.missing_pws_components ?? []).join(', ') || 'Brak'}</p>
      <p className="muted">Brakujące komponenty gotowości: {(coverage.missing_readiness_components ?? []).join(', ') || 'Brak'}</p>
      {quality?.component_availability ? (
        <div className="component-availability">
          {Object.entries(quality.component_availability).map(([key, value]) => (
            <span key={key}>{key}: {formatPercent(value.coverage_ratio ?? null)}</span>
          ))}
        </div>
      ) : null}
    </section>
  );
}
