# 15_build_dashboard_payload

This module builds a stable local dashboard presentation payload from existing analytical artifacts only. It does not recompute readiness, PWS components, PWS weights or PWS scores.

Deterministic PWS is always the primary score. An optional validated LLM-assisted PWS may be exposed only as a separately labelled comparison variant and must never replace the deterministic score.

The latest dashboard state follows the latest deterministic PWS date axis even when the latest date does not contain a numeric score because of insufficient coverage.

Missing values remain null and are never replaced with zero.

This module does not call an LLM, implement an API, build a user interface, generate medical diagnoses, predict injuries or produce training prescriptions.

## Purpose

The module aggregates existing local artifacts from load metrics, readiness, PWS components, PWS weights, deterministic PWS and the optional LLM-assisted PWS module. It produces a stable presentation contract for a future API or UI.

## Inputs

Required:

- `config/dashboard_payload_policy_v1.json`
- `data/pipeline/08_compute_load_metrics/load_metrics.json`
- `data/pipeline/08_compute_load_metrics/load_metrics_quality_report.json`
- `data/pipeline/09_compute_readiness/readiness.json`
- `data/pipeline/09_compute_readiness/readiness_quality_report.json`
- `data/pipeline/10_compute_pws_components/pws_components.json`
- `data/pipeline/10_compute_pws_components/pws_components_quality_report.json`
- `data/pipeline/11_compute_pws_weights/pws_weights.json`
- `data/pipeline/11_compute_pws_weights/pws_weights_quality_report.json`
- `data/pipeline/12_compute_pws_score/pws_score.json`
- `data/pipeline/12_compute_pws_score/pws_score_quality_report.json`

Optional:

- `data/pipeline/13_validate_llm_weight_influence/llm_assisted_pws.json`
- `data/pipeline/13_validate_llm_weight_influence/llm_assisted_pws_quality_report.json`
- `data/pipeline/13_validate_llm_weight_influence/llm_validation_report.json`
- `data/pipeline/13_validate_llm_weight_influence/openai_assisted_pws.json`
- `data/pipeline/13_validate_llm_weight_influence/openai_assisted_pws_quality_report.json`

## Payload Sections

- `metadata`
- `current_state`
- `time_series`
- `quality_and_coverage`
- `disclosures`

`current_state` is selected from the latest date on the deterministic PWS axis. If that date has no numeric PWS, the payload still exposes the latest date and its insufficient coverage.

## Optional Assisted PWS

Missing assisted artifacts, skipped LLM, no-adjustment and rejected proposals are non-blocking. A validated assisted score is shown only for its exact date and never replaces `primary_pws`.

The OpenAI artifact follows the same rule. It is exposed as `external_assisted_pws` in current state and time series, separately from the local `optional_assisted_pws`; neither variant changes the deterministic primary score.

The time series also copies the validated component weights for the deterministic, local LLM and OpenAI variants. These fields are presentation-only history; this module does not recalculate or normalize any weight.

## Commands

Run:

```bat
pipeline\15_build_dashboard_payload\run.bat
```

Tests:

```bat
py -m pytest tests\00_project_contract tests\01_find_input_workbook tests\02_read_xlsx_workbook tests\03_trim_workbook tests\04_garmin_activity_ingest tests\05_normalize_daily_records tests\06_normalize_activities tests\07_build_daily_features tests\08_compute_load_metrics tests\09_compute_readiness tests\10_compute_pws_components tests\11_compute_pws_weights tests\12_compute_pws_score tests\13_validate_llm_weight_influence tests\15_build_dashboard_payload
```

Visualization:

```bat
visualization\15_build_dashboard_payload\run_visualization.bat
```

The output artifacts contain private derived health, activity and wellness presentation data and are ignored by Git.
