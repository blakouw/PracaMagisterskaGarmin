# 07 Build Daily Features

Status: implemented.

This module builds the base daily feature table by joining normalized daily records with transparent daily activity aggregations. It does not calculate load metrics, readiness or PWS.

A day without normalized activities may contain zero activity counts and sums. A day with activities but missing activity values must preserve those aggregate values as null rather than silently assuming zero.

Missing physiological values remain null and must not be interpreted as negative health or performance signals by this module.

## Pipeline Role

Module 07 consumes `05_normalize_daily_records` as the primary source of dates and daily health fields. `06_normalize_activities` is an optional activity aggregation source. The table contains one feature row per date from module 05 only; activities assigned to dates outside that range are reported as orphan activity dates and do not create new daily rows.

## Inputs

Required:

- `config/daily_features_policy_v1.json`
- `data/pipeline/05_normalize_daily_records/daily_records.json`
- `data/pipeline/05_normalize_daily_records/daily_records_schema.json`
- `data/pipeline/05_normalize_daily_records/data_quality_report.json`

Optional:

- `data/pipeline/06_normalize_activities/activities_normalized.json`
- `data/pipeline/06_normalize_activities/activities_by_date.json`
- `data/pipeline/06_normalize_activities/activity_schema.json`
- `data/pipeline/06_normalize_activities/activity_data_quality_report.json`

The module does not open the workbook, read raw sheets, call Garmin API, parse FIT/TCX, use module 04 directly or depend on the previous project at runtime.

## Feature Model

Each `daily_feature` record copies all fields from module 05 without semantic change, then appends transparent activity aggregations:

- `activity_count`
- `activity_total_distance_km`
- `activity_total_duration_seconds`
- `activity_total_calories`
- `activity_total_elevation_gain_m`
- `activity_total_elevation_loss_m`
- `activity_total_hr_zone_1_seconds` through `activity_total_hr_zone_5_seconds`
- `activity_duration_weighted_average_hr_bpm`
- `activity_duration_weighted_average_power_w`
- `activity_duration_weighted_average_speed_kmh`
- `activity_maximum_hr_bpm`
- `activity_maximum_power_w`
- `activity_types_present`
- `activity_ids`

Sums include available numeric source values only. If a day has activities but every value for a summed field is missing, the aggregate is `null`. If the day has no activities, count and sums are technical zero values and weighted means/maxima are `null`.

## Outputs

- `daily_features.json`
- `daily_features.csv`
- optional `daily_features.parquet`
- `daily_features_schema.json`
- `daily_features_quality_report.json`
- `daily_features_lineage.json`
- `run_manifest.json`
- `run_log.txt`
- `errors.json`

JSON and CSV are required. Parquet is attempted only when optional `pandas` and `pyarrow` dependencies are available.

## Scope Exclusions

This module does not calculate RHR delta, LnRMSSD, acute load, chronic load, ACWR, EWMA ACWR, monotony, strain, readiness, LQ, REC, CAP, VS, PWS components, PWS weights or final PWS. It does not call LLM, build dashboard payloads, implement API or implement UI.

## Privacy

The feature table may contain private health, activity and training data. Generated artifacts are ignored by Git and must remain local.

## Run

```bat
pipeline\07_build_daily_features\run.bat
```

## Tests

```bat
python -m pytest tests\00_project_contract tests\01_find_input_workbook tests\02_read_xlsx_workbook tests\03_trim_workbook tests\04_garmin_activity_ingest tests\05_normalize_daily_records tests\06_normalize_activities tests\07_build_daily_features
```

## Visualization

```bat
visualization\07_build_daily_features\run_visualization.bat
```

Optional local debug can show a limited number of feature records:

```bat
python visualization\07_build_daily_features\preview_daily_features.py --show-records --limit 5
```
