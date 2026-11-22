# 09 Compute Readiness

This module computes a deterministic daily readiness score from available recovery and load-balance signals. Readiness is a short-term decision-support indicator and is not the same as PWS.

## Pipeline Position

Module 09 consumes `08_compute_load_metrics` artifacts and writes readiness artifacts for `10_compute_pws_components`. It does not read Garmin workbooks, API artifacts, FIT/TCX files or earlier raw data.

## Inputs

- `config/readiness_policy_v1.json`
- `data/pipeline/08_compute_load_metrics/load_metrics.json`
- `data/pipeline/08_compute_load_metrics/load_metrics_schema.json`
- `data/pipeline/08_compute_load_metrics/load_metrics_quality_report.json`
- `data/pipeline/08_compute_load_metrics/load_metrics_lineage.json`

## Components and Weights

- `hrv`: 0.363636
- `stress`: 0.272727
- `rhr`: 0.181818
- `load_balance`: 0.181818

Missing readiness components remain null and are never replaced with zero. The final readiness score is computed only when the configured minimum data availability requirements are satisfied.

Minimum requirements are at least 3 available components and at least 0.50 available base-weight sum. Available component weights are renormalized by dividing each available base weight by the available base-weight sum.

## Component Rules

- HRV prefers `hrv_last_night_avg_ms` against the balanced baseline band; if unavailable, it uses nightly HRV relative to `hrv_weekly_avg_ms`.
- Stress uses `100 - avg_stress`, clipped to 0..100.
- RHR uses an internal delta against `resting_hr_baseline_bpm` and subtracts 8 points per bpm above baseline.
- Load balance prefers `acwr_ewma`; `acwr_rolling` is only a fallback. It does not recalculate ACWR.

Labels are `low/niska`, `reduced/obnizona`, `moderate/umiarkowana`, `high/wysoka`, and `insufficient_data`.

Readiness is not a medical diagnosis, injury prediction or professional training prescription.

## Outputs

- `data/pipeline/09_compute_readiness/readiness.json`
- `data/pipeline/09_compute_readiness/readiness.csv`
- `data/pipeline/09_compute_readiness/readiness.parquet`, if optional dependencies are available
- `data/pipeline/09_compute_readiness/readiness_schema.json`
- `data/pipeline/09_compute_readiness/readiness_quality_report.json`
- `data/pipeline/09_compute_readiness/readiness_lineage.json`
- `data/pipeline/09_compute_readiness/run_manifest.json`
- `data/pipeline/09_compute_readiness/run_log.txt`
- `data/pipeline/09_compute_readiness/errors.json`

The artifacts contain private health and training data and must remain local.

## Explicit Non-Responsibilities

This module does not calculate PWS components, PWS weights or any LLM-based adjustment. It does not generate medical diagnoses, training prescriptions, coach messages, dashboard payloads, API responses or UI views.

## Run

```bat
pipeline\09_compute_readiness\run.bat
```

## Tests

```bat
python -m pytest tests\09_compute_readiness
```

## Visualization

```bat
visualization\09_compute_readiness\run_visualization.bat
```
