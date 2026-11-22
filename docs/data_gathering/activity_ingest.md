# 04 Garmin Activity Ingest

Status: implemented. Optional module.

This module optionally downloads raw extended Garmin activity artifacts. It does not normalize activities, calculate metrics or block the workbook-based pipeline when API ingest is unavailable.

The main project path remains the local Garmin workbook. This module is only an optional enrichment source for future activity normalization.

## Inputs

- `config/garmin_activity_ingest_v1.json`
- local tokenstore in `data/local_secrets/garmin_tokenstore/` when ingest is enabled
- optional `data/pipeline/03_trim_workbook/trimmed_sheets_manifest.json`
- optional `data/pipeline/03_trim_workbook/trimmed_sheets/Activities.csv`

The tokenstore directory may contain local `oauth1_token.json` and `oauth2_token.json`. Required logical fields are `oauth_token`, `oauth_token_secret`, `access_token` and `refresh_token`. Token values are never written to pipeline artifacts or logs.

A tokenstore from a previous project may be copied here once as a local secret bootstrap step. The new module must then use only `data/local_secrets/garmin_tokenstore/`; it must not import, run or depend on the previous project at runtime.

## Configuration

`config/garmin_activity_ingest_v1.json` is public and contains no secrets. It defaults to `enabled: false`, so the module writes a controlled `skipped_disabled` manifest without reading credentials, importing `garminconnect` or calling the network.

Activity IDs may come from:

- `manual_activity_ids` in the public config
- the `activityId` column from a trimmed `Activities.csv` produced by module 03

IDs are deduplicated and sorted deterministically. Empty or invalid IDs are skipped and reported as warnings.

## Downloaded Artifacts

When enabled, configured, and authenticated, the module can request:

- `details.json`
- `splits.json`
- `activity.fit`
- `activity.tcx`
- per-activity `download_manifest.json`

Each activity is stored under `data/pipeline/04_garmin_activity_ingest/activities/<activity_id>/`.

## Status Behavior

- `skipped_disabled`: public config disables ingest; this is the default.
- `skipped_dependency_unavailable`: optional `garminconnect` is not installed.
- `skipped_missing_credentials`: local tokenstore is absent or incomplete.
- `skipped_no_activity_ids`: no valid activity IDs are configured or available from module 03.
- `completed`: all requested activity artifacts were downloaded.
- `completed_with_failures`: some requested downloads failed, but the module preserved successful artifacts.

All `skipped_*` statuses have `execution_status: success` and do not block the workbook-based pipeline.

## Privacy And Scope

Downloaded activity artifacts can contain private health and location data. They are ignored by Git. The module does not normalize activity data, merge workbook and API data, calculate metrics, readiness or PWS, call LLM, implement auth UI, implement backend API or implement dashboard UI.

## Run

```bat
pipeline\04_garmin_activity_ingest\run.bat
```

## Tests

```bat
python -m pytest tests\00_project_contract tests\01_find_input_workbook tests\02_read_xlsx_workbook tests\03_trim_workbook tests\04_garmin_activity_ingest
```

## Visualization

```bat
visualization\04_garmin_activity_ingest\run_visualization.bat
```
