# 10 Compute PWS Components

This module computes the four auditable PWS components LQ, REC, CAP and VS only. It does not calculate component weights or final PWS.

## Inputs

- `config/pws_components_policy_v1.json`
- `data/pipeline/08_compute_load_metrics/load_metrics.json`
- `data/pipeline/08_compute_load_metrics/load_metrics_schema.json`
- `data/pipeline/08_compute_load_metrics/load_metrics_quality_report.json`
- `data/pipeline/08_compute_load_metrics/load_metrics_lineage.json`
- `data/pipeline/09_compute_readiness/readiness.json`
- `data/pipeline/09_compute_readiness/readiness_schema.json`
- `data/pipeline/09_compute_readiness/readiness_quality_report.json`
- `data/pipeline/09_compute_readiness/readiness_lineage.json`

LQ represents load quality from existing ACWR metrics, REC inherits deterministic readiness, CAP is a duration-based performed-capacity proxy relative to personal baseline, and VS measures stability of available vital signals against personal historical baselines.

## Components

- `LQ`: prefers `acwr_ewma`; falls back to `acwr_rolling`. `monotony_7d` and `strain_7d` are retained as audit context only and do not affect LQ in version 1.
- `REC`: directly inherits `readiness_score`; it does not recompute readiness.
- `CAP`: uses `activity_total_duration_seconds`, comparing the latest 7 calendar days to the weekly equivalent of the prior 21 calendar days. It is not VO2max, fitness diagnosis or training quality.
- `VS`: uses personal prior-28-day baselines for `resting_hr_bpm`, `hrv_last_night_avg_ms`, `avg_sleep_spo2` and `avg_sleep_respiration`; at least 14 historical observations are required per signal.

Missing component values remain null and are never replaced with zero.

Known overlap between LQ, REC and VS is disclosed for later weighting and is intentionally not resolved in this module.

The module does not use LLM, generate medical diagnoses, predict injuries or produce training prescriptions.

## Outputs

- `data/pipeline/10_compute_pws_components/pws_components.json`
- `data/pipeline/10_compute_pws_components/pws_components.csv`
- `data/pipeline/10_compute_pws_components/pws_components.parquet`, if optional dependencies are available
- `data/pipeline/10_compute_pws_components/pws_components_schema.json`
- `data/pipeline/10_compute_pws_components/pws_components_quality_report.json`
- `data/pipeline/10_compute_pws_components/pws_components_lineage.json`
- `data/pipeline/10_compute_pws_components/run_manifest.json`
- `data/pipeline/10_compute_pws_components/run_log.txt`
- `data/pipeline/10_compute_pws_components/errors.json`

Generated artifacts contain private health and training data and must remain local.

## Run

```bat
pipeline\10_compute_pws_components\run.bat
```

## Tests

```bat
python -m pytest tests\10_compute_pws_components
```

## Visualization

```bat
visualization\10_compute_pws_components\run_visualization.bat
```
