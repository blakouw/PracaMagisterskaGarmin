# 08_compute_load_metrics

This module computes transparent load metrics from a policy-selected daily load. Complete daily session-RPE is preferred; `active_kcal` remains the explicit fallback when any activity lacks RPE or a positive duration.

## Pipeline Position

Module 08 consumes the base daily feature table from `07_build_daily_features` and optionally reads normalized activity RPE and duration from `06_normalize_activities`. It writes load-metric artifacts for `09_compute_readiness` and does not call Garmin or an LLM.

## Load Selection

For each activity with complete inputs:

`session_rpe = perceived_effort_rpe * duration_seconds / 60`

For a calendar day, `load_session_rpe` is the sum over all activities only when every activity has valid RPE and duration. Otherwise `load_value` uses the existing `active_kcal` proxy for the entire day. No partial day mixes the two sources, and `load_source` records the selected branch.

No-activity days and missing activity artifacts also use the labelled `active_kcal_fallback`. Missing RPE is never represented as zero.

The two sources use different proxy units. The source label, coverage counts, raw active kilocalories and optional session-RPE value are retained in JSON, CSV, quality and lineage artifacts so transitions remain auditable.

## Metrics

Rolling ACWR and EWMA ACWR remain separate. All existing acute/chronic, ACWR, monotony and strain calculations now consume `load_value`. Complete calendar windows are still required, missing dates are not filled, and zero-variance monotony remains unavailable.

ACWR zones are descriptive decision-support categories, not injury predictions, diagnoses or training prescriptions.

## Inputs

- `config/load_metrics_policy_v1.json`
- required module 07 daily feature artifacts
- optional `data/pipeline/06_normalize_activities/activities_normalized.json`

## Outputs

- `load_metrics.json`, `load_metrics.csv` and optional Parquet
- schema, quality, lineage, run manifest, log and errors under `data/pipeline/08_compute_load_metrics/`

The artifacts contain private health and training data and must remain local.

## Run

```bat
pipeline\08_compute_load_metrics\run.bat
```

## Tests

```bat
python -m pytest tests\08_compute_load_metrics
```
