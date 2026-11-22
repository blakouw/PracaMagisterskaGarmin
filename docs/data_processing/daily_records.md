# 05 Normalize Daily Records

Status: implemented.

This module normalizes approved daily Garmin source fields into one record per date from Daily_Summary. It does not normalize activities or calculate derived metrics.

Missing health or activity data is preserved as null and must not be interpreted as a zero score or a negative health signal by this module.

## Pipeline Role

Module 05 consumes the approved CSV artifacts from `03_trim_workbook` and writes a stable daily-record table for later feature building. Module `04_garmin_activity_ingest` is optional and is not consumed here.

## Inputs

- `data/pipeline/03_trim_workbook/trimmed_sheets_manifest.json`
- `data/pipeline/03_trim_workbook/trimmed_sheets/*.csv`, excluding `Activities.csv`
- `config/garmin_daily_normalization_v1.json`

The original workbook, raw XLSX XML, Garmin API artifacts and previous project files are not read.

## Daily Model

`Daily_Summary` is the only axis for creating daily records. The source date column `calendarDate` becomes `date` in `YYYY-MM-DD` format. Optional daily sheets are left-joined to those dates only. Dates that appear only in optional sheets are reported as orphan optional rows and do not create new daily records.

Duplicate dates in consumed daily sheets are blocking. Invalid primary dates are blocking. Optional rows with invalid dates are excluded and reported.

## Field Mapping

The public policy maps exact source column names to stable fields such as `active_kcal`, `steps`, `sleep_seconds`, `hrv_weekly_avg_ms`, `avg_spo2`, `moderate_minutes` and `weight_kg`. No fuzzy matching or hidden semantic inference is performed.

Conflicts between sources are resolved by `field_source_priority` in the policy and reported in `data_quality_report.json`.

The only allowed unit conversion is body weight normalization: numeric values greater than `400` are treated as grams and divided by `1000`; otherwise they are treated as kilograms.

## Outputs

- `daily_records.json`
- `daily_records.csv`
- `daily_records_schema.json`
- `data_quality_report.json`
- `run_manifest.json`
- `run_log.txt`
- `errors.json`

Private Garmin-derived records are ignored by Git and must remain local.

## Scope Exclusions

This module does not process `Activities`, FIT, TCX, `details.json` or `splits.json`. It does not call Garmin API, normalize activities, calculate RHR delta, LnRMSSD, load metrics, ACWR, readiness, PWS or PWS weights. It does not use LLM and does not implement backend API or UI.

## Run

```bat
pipeline\05_normalize_daily_records\run.bat
```

## Tests

```bat
python -m pytest tests\00_project_contract tests\01_find_input_workbook tests\02_read_xlsx_workbook tests\03_trim_workbook tests\04_garmin_activity_ingest tests\05_normalize_daily_records
```

## Visualization

```bat
visualization\05_normalize_daily_records\run_visualization.bat
```

Optional local debug can show a small sample of records:

```bat
python visualization\05_normalize_daily_records\preview_daily_records.py --show-records --limit 5
```

That debug output may contain private health and activity data.
