# 06 Normalize Activities

Status: implemented.

This module normalizes available activity source artifacts into stable activity records and date-grouped outputs. It does not calculate training load, readiness or PWS.

FIT and TCX files are referenced as raw local artifacts only and are not parsed in this module.

Missing activity values are preserved as null and must not be interpreted as zero-performance or zero-training signals by this module.

## Pipeline Role

Module 06 prepares the activity stream for later feature building. It does not depend on `05_normalize_daily_records` as an input; daily records and activities remain separate artifacts at this stage.

## Sources

- optional `data/pipeline/03_trim_workbook/trimmed_sheets/Activities.csv`
- optional `data/pipeline/04_garmin_activity_ingest/activity_ingest_manifest.json`
- optional local `details.json` and `splits.json` referenced by module 04
- optional FIT and TCX paths as references only

No network calls are made. Module 04 remains optional. If no activity source exists, the module writes empty valid outputs with `normalized_empty_no_activity_sources` and `ready_for_next_module: true`.

## Policy

`config/garmin_activity_normalization_v1.json` defines exact source mappings, source priority, unit conversions, split mapping and FIT/TCX handling. No fuzzy matching is performed.

Workbook activity fields are preferred for UI-facing values. API details may fill missing fields or create API-only records when both `activity_id` and `start_time_local` are available. Conflicts are reported in `activity_data_quality_report.json` and resolved by configured source priority.

## Model

Each `normalized_activity` includes identity, local date, source presence, converted distance/speed/duration fields, HR, power, elevation, HR zone seconds, optional splits, API artifact references, field sources and warnings.

Activities are grouped by the local calendar date extracted from `start_time_local`; no UTC conversion or day shifting is performed.

## Outputs

- `activities_normalized.json`
- `activities_normalized.csv`
- `activities_by_date.json`
- `activity_schema.json`
- `activity_data_quality_report.json`
- `run_manifest.json`
- `run_log.txt`
- `errors.json`

## Scope Exclusions

This module does not parse FIT or TCX, download Garmin API data, normalize daily records, build daily features, calculate load, ACWR, monotony, strain, readiness, PWS or use LLM. The new project does not depend on the previous project at runtime.

## Run

```bat
pipeline\06_normalize_activities\run.bat
```

## Tests

```bat
python -m pytest tests\00_project_contract tests\01_find_input_workbook tests\02_read_xlsx_workbook tests\03_trim_workbook tests\04_garmin_activity_ingest tests\05_normalize_daily_records tests\06_normalize_activities
```

## Visualization

```bat
visualization\06_normalize_activities\run_visualization.bat
```

Optional local debug can show limited activity records:

```bat
python visualization\06_normalize_activities\preview_activities.py --show-activities --limit 5
```

That debug output may contain private sport and location-related data. FIT and TCX contents are never printed.
