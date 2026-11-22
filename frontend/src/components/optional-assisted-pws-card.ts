import { Component, computed, input } from '@angular/core';
import type { OptionalAssistedPws } from '../api/dashboardTypes';
import { formatNumber, formatScore, titleCase } from '../utils/formatters';
import { formatPwsComponentLabel } from '../utils/pwsLabels';

const statusLabels: Record<string, string> = {
  not_available_no_assisted_artifact: 'Analiza LLM nie została uruchomiona',
  not_available_no_adjustment_proposed: 'Nie zaproponowano korekty',
  not_available_proposal_rejected: 'Propozycja nie miała kompletnej postaci numerycznej',
  not_available_for_current_date: 'Wariant niedostępny dla aktualnej daty',
  available_no_adjustment_same_as_deterministic: 'Korekta nie była potrzebna',
  error_llm_no_assisted_score_delivered: 'LLM nie dostarczył wartości asystowanego PWS'
};

@Component({
  selector: 'app-optional-assisted-pws-card',
  host: { class: 'dashboard-section' },
  templateUrl: './optional-assisted-pws-card.html'
})
export class OptionalAssistedPwsCard {
  readonly assisted = input.required<OptionalAssistedPws>();
  protected readonly formatScore = formatScore;
  protected readonly formatNumber = formatNumber;
  protected readonly titleCase = titleCase;
  protected readonly formatPwsComponentLabel = formatPwsComponentLabel;
  protected readonly entries = Object.entries;
  protected readonly failed = computed(() => {
    const data = this.assisted();
    return data.status === 'error_llm_no_assisted_score_delivered' || Boolean(data.llm_error);
  });
  protected readonly statusDescription = computed(() => {
    const { llm_error, status } = this.assisted();
    if (llm_error === 'LLM did not deliver assisted PWS values.') return 'LLM nie dostarczył wartości assisted PWS.';
    return llm_error || statusLabels[status] || status.replace(/_/g, ' ');
  });
  protected readonly disclosure = computed(() => {
    const data = this.assisted();
    if (data.status === 'available_no_adjustment_same_as_deterministic') {
      return 'LLM potwierdził, że ograniczona zmiana wag nie jest potrzebna; wariant porównawczy jest zgodny z deterministycznym PWS.';
    }
    if (data.proposal_interpretation_mode === 'permissive_simplex_normalization') {
      return 'Surowa propozycja przekroczyła standardowe progi. Nie została pominięta: wagi znormalizowano deterministycznie, a wszystkie ostrzeżenia zachowano w audycie.';
    }
    return 'Ten wariant nie zastępuje deterministycznego PWS.';
  });
  protected readonly weightSections = computed(() => {
    const data = this.assisted();
    return [
      { title: 'Surowe zmiany wag zaproponowane przez LLM', values: data.raw_proposed_weight_deltas },
      { title: 'Efektywne zmiany wag po normalizacji', values: data.effective_weight_deltas },
      { title: 'Wagi użyte do wariantu asystowanego', values: data.validated_adjusted_weights }
    ];
  });
}
