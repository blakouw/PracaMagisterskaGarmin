import type { OptionalAssistedPws } from '../api/dashboardTypes';
import { formatNumber, formatScore, titleCase } from '../utils/formatters';
import { formatPwsComponentLabel } from '../utils/pwsLabels';

interface Props {
  assisted: OptionalAssistedPws;
}

function errorText(error: string | null | undefined): string | null {
  if (!error) return null;
  if (error === 'LLM did not deliver assisted PWS values.') return 'LLM nie dostarczył wartości assisted PWS.';
  return error;
}

function statusText(status: string): string {
  if (status === 'not_available_no_assisted_artifact') return 'Analiza LLM nie została uruchomiona';
  if (status === 'not_available_no_adjustment_proposed') return 'Nie zaproponowano korekty';
  if (status === 'not_available_proposal_rejected') return 'Propozycja nie miała kompletnej postaci numerycznej';
  if (status === 'not_available_for_current_date') return 'Wariant niedostępny dla aktualnej daty';
  if (status === 'available_no_adjustment_same_as_deterministic') return 'Korekta nie była potrzebna';
  if (status === 'error_llm_no_assisted_score_delivered') return 'LLM nie dostarczył wartości asystowanego PWS';
  return status.replace(/_/g, ' ');
}

function WeightValues({ values }: { values: Record<string, number> }) {
  return (
    <div className="metric-grid">
      {Object.entries(values).map(([key, value]) => (
        <span key={key}>
          {formatPwsComponentLabel(key)}: {formatNumber(value, 3)}
        </span>
      ))}
    </div>
  );
}

export function OptionalAssistedPwsCard({ assisted }: Props) {
  if (!assisted.available) {
    const failed = assisted.status === 'error_llm_no_assisted_score_delivered' || Boolean(assisted.llm_error);
    return (
      <section className="card secondary-card" aria-label="Status PWS asystowanego przez LLM">
        <p className="eyebrow">Wariant porównawczy</p>
        <h2>{failed ? 'LLM-assisted PWS niedostępny' : 'Brak wariantu asystowanego'}</h2>
        <p className={failed ? 'notice error-banner' : 'muted'}>{errorText(assisted.llm_error) ?? statusText(assisted.status)}</p>
        {assisted.llm_tool_execution?.attempted ? (
          <p className="muted">Zapis wyniku: {assisted.llm_tool_execution.succeeded ? 'udany' : 'nieudany'}</p>
        ) : null}
      </section>
    );
  }

  const noAdjustment = assisted.status === 'available_no_adjustment_same_as_deterministic';
  const normalized = assisted.proposal_interpretation_mode === 'permissive_simplex_normalization';

  return (
    <section className="card secondary-card" aria-label="Opcjonalny wariant PWS asystowany przez LLM">
      <div className="card-heading">
        <div>
          <h2>PWS asystowany przez LLM</h2>
        </div>
      </div>
      <p className="muted">Analiza PWS asystowana przez LLM jest gotowa.</p>
      <div className="score-value secondary">{formatScore(assisted.score ?? null)}</div>
      <p className="score-label">{titleCase(assisted.label)}</p>
      <p className="muted">Różnica względem wyniku deterministycznego: {formatNumber(assisted.delta_from_deterministic ?? null, 2)}</p>
      <p className="notice">
        {noAdjustment
          ? 'LLM potwierdził, że ograniczona zmiana wag nie jest potrzebna; wariant porównawczy jest zgodny z deterministycznym PWS.'
          : normalized
            ? 'Surowa propozycja przekroczyła standardowe progi. Nie została pominięta: wagi znormalizowano deterministycznie, a wszystkie ostrzeżenia zachowano w audycie.'
            : 'Ten wariant nie zastępuje deterministycznego PWS.'}
      </p>
      {assisted.validation_warnings?.length ? (
        <details>
          <summary>Ostrzeżenia walidacji ({assisted.validation_warnings.length})</summary>
          <ul>
            {assisted.validation_warnings.map((warning, index) => (
              <li key={`${index}-${warning}`}>{warning}</li>
            ))}
          </ul>
        </details>
      ) : null}
      {assisted.llm_reason_summary ? <p className="muted">Uzasadnienie LLM: {assisted.llm_reason_summary}</p> : null}
      {assisted.llm_tool_execution ? (
        <p className="muted">Zapis wyniku: {assisted.llm_tool_execution.succeeded ? 'udany' : 'nieudany'}</p>
      ) : null}
      {assisted.raw_proposed_weight_deltas ? (
        <details>
          <summary>Surowe zmiany wag zaproponowane przez LLM</summary>
          <WeightValues values={assisted.raw_proposed_weight_deltas} />
        </details>
      ) : null}
      {assisted.effective_weight_deltas ? (
        <details>
          <summary>Efektywne zmiany wag po normalizacji</summary>
          <WeightValues values={assisted.effective_weight_deltas} />
        </details>
      ) : null}
      {assisted.validated_adjusted_weights ? (
        <details>
          <summary>Wagi użyte do wariantu asystowanego</summary>
          <WeightValues values={assisted.validated_adjusted_weights} />
        </details>
      ) : null}
      {assisted.conversation_log_path ? (
        <p className="muted">Log analizy dnia: <code>{assisted.conversation_log_path}</code></p>
      ) : null}
    </section>
  );
}
