export type NullableNumber = number | null;
export type NullableString = string | null;

export interface ApiHealthResponse {
  service: string;
  api_version: string;
  status: 'ok' | 'degraded' | string;
  local_only: boolean;
  read_only: boolean;
  snapshot_available: boolean;
  snapshot_id?: string;
  latest_data_date?: string;
  primary_score_type?: string;
  optional_assisted_score_available?: boolean;
  snapshot_error_code?: string;
}

export interface SnapshotStatus {
  snapshot_id: string;
  snapshot_version?: string;
  published_at?: string;
  latest_data_date: string;
  payload_ready: boolean;
  primary_pws: {
    score_type: string;
    computed: boolean;
    score: NullableNumber;
    label_id: NullableString;
    label: NullableString;
    coverage_tier: NullableString;
  };
  optional_assisted_pws?: {
    available: boolean;
    score?: NullableNumber;
    label_id?: NullableString;
    label?: NullableString;
    must_not_replace_primary_score: boolean;
  };
  records_count?: number;
}

export interface PrimaryPws {
  score_type: 'deterministic' | string;
  score_field: string;
  score: NullableNumber;
  computed: boolean;
  status: string;
  label_id: NullableString;
  label: NullableString;
  coverage_ratio: NullableNumber;
  coverage_tier: NullableString;
  computed_from_partial_coverage?: boolean;
  available_components?: string[];
  missing_components?: string[];
  weighted_contributions?: Record<string, number>;
  display_disclosure?: string;
}

export interface LlmToolExecution {
  tool_name?: string;
  attempted?: boolean;
  succeeded?: boolean;
  error?: string | null;
}

export interface OptionalAssistedPws {
  available: boolean;
  score_type?: 'llm_assisted' | string;
  score_field?: string;
  score?: NullableNumber;
  computed?: boolean;
  status: string;
  analysis_status?: string;
  label_id?: NullableString;
  label?: NullableString;
  delta_from_deterministic?: NullableNumber;
  validated_adjusted_weights?: Record<string, number>;
  raw_proposed_weight_deltas?: Record<string, number>;
  effective_weight_deltas?: Record<string, number>;
  proposal_interpretation_mode?: string | null;
  validation_warnings?: string[];
  conversation_log_path?: string | null;
  llm_response_decision?: string | null;
  llm_reason_summary?: string | null;
  llm_tool_execution?: LlmToolExecution | null;
  llm_error?: string | null;
  latest_assisted_date?: string;
  must_not_replace_primary_score: boolean;
  display_disclosure?: string;
  provider?: string;
  model?: string | null;
  must_not_replace_local_llm_variant?: boolean;
}

export interface ReadinessState {
  score?: NullableNumber;
  readiness_score?: NullableNumber;
  score_field?: string;
  computed?: boolean;
  status?: string;
  readiness_status?: string;
  label_id?: NullableString;
  readiness_label_id?: NullableString;
  label?: NullableString;
  readiness_label?: NullableString;
  coverage_ratio?: NullableNumber;
  readiness_coverage_ratio?: NullableNumber;
  available_components?: string[];
  available_readiness_components?: string[];
  missing_components?: string[];
  missing_readiness_components?: string[];
  display_disclosure?: string;
}

export interface PwsComponentItem {
  name: string;
  score: NullableNumber;
  status: string;
}

export interface PwsComponentsState {
  LQ?: PwsComponentItem;
  REC?: PwsComponentItem;
  CAP?: PwsComponentItem;
  VS?: PwsComponentItem;
  available_components?: string[];
  missing_components?: string[];
  coverage_ratio?: NullableNumber;
  known_overlaps?: string[];
}

export interface PwsWeightsState {
  base_weights?: Record<string, number> | null;
  deterministic_effective_weights?: Record<string, number> | null;
  weights_ready_for_final_pws?: boolean;
  weights_readiness_status?: string;
  movement_limits_applied?: boolean;
  overlap_controls_applied?: string[];
  llm_adjustment_eligible?: boolean;
  display_disclosure?: string;
}

export interface LoadMetricsState {
  acwr_ewma?: NullableNumber;
  acwr_rolling?: NullableNumber;
  acute_ewma_7d?: NullableNumber;
  chronic_ewma_28d?: NullableNumber;
  monotony_7d?: NullableNumber;
  strain_7d?: NullableNumber;
  display_disclosure?: string;
}

export interface CoverageState {
  pws_coverage_tier?: NullableString;
  pws_coverage_ratio?: NullableNumber;
  pws_computed_from_partial_coverage?: boolean;
  readiness_coverage_ratio?: NullableNumber;
  pws_components_coverage_ratio?: NullableNumber;
  missing_pws_components?: string[];
  missing_readiness_components?: string[];
}

export interface DashboardCurrentState {
  date: string;
  primary_pws: PrimaryPws;
  optional_assisted_pws: OptionalAssistedPws;
  external_assisted_pws?: OptionalAssistedPws;
  readiness: ReadinessState;
  pws_components: PwsComponentsState;
  pws_weights: PwsWeightsState;
  load_metrics: LoadMetricsState;
  coverage: CoverageState;
  source_statuses?: Record<string, unknown>;
  disclosures: string[];
}

export interface TimeSeriesRecord {
  date: string;
  pws_deterministic: NullableNumber;
  pws_deterministic_computed?: boolean;
  pws_label_id?: NullableString;
  pws_label?: NullableString;
  pws_coverage_ratio?: NullableNumber;
  pws_coverage_tier?: NullableString;
  pws_computed_from_partial_coverage?: boolean;
  readiness_score?: NullableNumber;
  readiness_status?: string;
  readiness_label_id?: NullableString;
  readiness_label?: NullableString;
  readiness_coverage_ratio?: NullableNumber;
  lq_score?: NullableNumber;
  rec_score?: NullableNumber;
  cap_score?: NullableNumber;
  vs_score?: NullableNumber;
  weight_lq?: NullableNumber;
  weight_rec?: NullableNumber;
  weight_cap?: NullableNumber;
  weight_vs?: NullableNumber;
  local_llm_weight_lq?: NullableNumber;
  local_llm_weight_rec?: NullableNumber;
  local_llm_weight_cap?: NullableNumber;
  local_llm_weight_vs?: NullableNumber;
  openai_weight_lq?: NullableNumber;
  openai_weight_rec?: NullableNumber;
  openai_weight_cap?: NullableNumber;
  openai_weight_vs?: NullableNumber;
  acwr_ewma?: NullableNumber;
  acwr_rolling?: NullableNumber;
  acute_ewma_7d?: NullableNumber;
  chronic_ewma_28d?: NullableNumber;
  monotony_7d?: NullableNumber;
  strain_7d?: NullableNumber;
  resting_hr_bpm?: NullableNumber;
  resting_hr_baseline_bpm?: NullableNumber;
  sleep_seconds?: NullableNumber;
  deep_sleep_seconds?: NullableNumber;
  light_sleep_seconds?: NullableNumber;
  rem_sleep_seconds?: NullableNumber;
  awake_sleep_seconds?: NullableNumber;
  hrv_last_night_avg_ms?: NullableNumber;
  hrv_weekly_avg_ms?: NullableNumber;
  avg_sleep_spo2?: NullableNumber;
  avg_sleep_respiration?: NullableNumber;
  avg_stress?: NullableNumber;
  max_stress?: NullableNumber;
  activity_duration_weighted_average_hr_bpm?: NullableNumber;
  activity_maximum_hr_bpm?: NullableNumber;
  activity_total_duration_seconds?: NullableNumber;
  activity_total_distance_km?: NullableNumber;
  steps?: NullableNumber;
  weight_kg?: NullableNumber;
  rhr_readiness_score?: NullableNumber;
  hrv_readiness_score?: NullableNumber;
  stress_readiness_score?: NullableNumber;
  load_balance_readiness_score?: NullableNumber;
  optional_assisted_pws?: NullableNumber;
  optional_assisted_label_id?: NullableString;
  optional_assisted_delta_from_deterministic?: NullableNumber;
  external_assisted_pws?: NullableNumber;
  external_assisted_label_id?: NullableString;
  external_assisted_delta_from_deterministic?: NullableNumber;
}

export interface TimeSeriesResponse {
  snapshot_id: string;
  filters: {
    date_from?: string | null;
    date_to?: string | null;
    limit?: number | null;
  };
  records_count: number;
  records: TimeSeriesRecord[];
}

export interface DashboardQualityAndCoverage {
  records_count?: number;
  presentation_availability?: {
    primary_pws_computed_count?: number;
    primary_pws_unavailable_count?: number;
    optional_assisted_score_count?: number;
    current_state_primary_pws_available?: boolean;
    current_state_optional_assisted_pws_available?: boolean;
  };
  coverage_tiers?: {
    full?: number;
    partial_eligible?: number;
    insufficient?: number;
  };
  pws_label_counts?: Record<string, number>;
  readiness_availability?: Record<string, number>;
  component_availability?: Record<string, { available_count?: number; coverage_ratio?: number }>;
  weight_availability?: Record<string, number>;
  optional_llm_assisted?: Record<string, unknown>;
  source_warnings?: string[];
  payload_warnings?: string[];
}

export type DashboardDisclosures = Record<string, string | boolean | string[]>;


export interface DashboardChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface DashboardChatRequest {
  message: string;
  history?: DashboardChatMessage[];
}

export interface DashboardChatResponse {
  snapshot_id?: string;
  latest_data_date?: string;
  answer: string;
  model?: string;
  provider?: string;
  tools_used?: string[];
  llm_called?: boolean;
  persisted?: boolean;
  snapshot_modified?: boolean;
  pipeline_triggered?: boolean;
  forbidden_action_confirmation?: Record<string, boolean>;
}
