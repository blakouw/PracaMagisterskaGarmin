# 17 Local API Server

Status: implemented.

This API is local-only and read-only. It binds to 127.0.0.1 by default and is not approved for public or network exposure without a separate security and deployment design.

This module serves the published current dashboard snapshot only. It does not trigger the pipeline, modify snapshots or recompute analytical values.

Deterministic PWS remains the primary score. An optional validated LLM-assisted PWS, when present in the snapshot, remains a separate comparison variant and must never replace the deterministic score.

The API loads and validates one published current snapshot at startup and serves that immutable in-memory view during the process lifetime. Restart the local API process after publishing a new snapshot.

This module does not implement authentication, user profiles, Garmin token management, a frontend, medical diagnoses, injury predictions, coaching messages or training prescriptions.

## Pipeline Role

This module runs after `16_persist_local_snapshot`. Its runtime source is only `data/published/dashboard_snapshots/current/`. It does not fall back to analytical pipeline artifacts, does not run previous modules, and does not read from the previous RepoMagi application runtime.

The public API policy is `config/dashboard_snapshot_api_policy_v1.json`. The snapshot publication policy remains `config/dashboard_snapshot_policy_v1.json`.

## Inputs

- `config/dashboard_snapshot_api_policy_v1.json`
- `config/dashboard_snapshot_policy_v1.json`
- `data/published/dashboard_snapshots/current/dashboard_payload.json`
- `data/published/dashboard_snapshots/current/snapshot_manifest.json`
- `data/published/dashboard_snapshots/current/snapshot_status.json`
- `data/published/dashboard_snapshots/current/snapshot_source_hashes.json`
- `data/published/dashboard_snapshots/current/dashboard_payload_schema.json`
- `data/published/dashboard_snapshots/current/dashboard_payload_quality_report.json`
- `data/published/dashboard_snapshots/current/dashboard_payload_lineage.json`
- `data/published/dashboard_snapshots/current/dashboard_time_series.csv`
- optional `data/published/dashboard_snapshots/current/dashboard_time_series.parquet`

## Startup Validation

At startup the module validates that required current snapshot files exist, JSON files parse, `snapshot_status.payload_ready` is true, the primary PWS score type is `deterministic`, the dashboard payload has required sections, the optional assisted PWS cannot replace primary, and the published hash artifact reports verified required hashes.

`--verify-file-hashes-on-startup` can re-check file hashes for debugging. The default validation trusts the published integrity artifact and does not rehash every file on each request.

If the current snapshot is missing or invalid, `/api/v1/health` remains available with `snapshot_available: false`, while data endpoints return `503`.

## Endpoints

- `GET /api/v1/health`
- `GET /api/v1/snapshot/status`
- `GET /api/v1/snapshot/manifest`
- `GET /api/v1/dashboard`
- `GET /api/v1/dashboard/current-state`
- `GET /api/v1/dashboard/time-series`
- `GET /api/v1/dashboard/quality`
- `GET /api/v1/dashboard/disclosures`

`/api/v1/dashboard/time-series` accepts read-only presentation filters:

- `date_from=YYYY-MM-DD`
- `date_to=YYYY-MM-DD`
- `limit=<integer>` up to `10000`

The endpoint filters existing records only. It does not interpolate, fill missing values, aggregate, or recompute trends.

## Exclusions

There are no write, auth, profile, token, pipeline-trigger, LLM, coaching, recommendation, diagnosis, injury prediction, public deployment, or frontend endpoints.

The removed `auth_and_profile_api` and `garmin_token_pipeline` modules are not restored here.

Missing values are preserved as `null` and are never replaced with `0`.

## Commands

Validate without starting the server:

```bat
pipeline\17_local_api_server\run.bat --validate-only
```

Validate with file hash checks:

```bat
pipeline\17_local_api_server\run.bat --validate-only --verify-file-hashes-on-startup
```

Run local API:

```bat
pipeline\17_local_api_server\run.bat
```

Run on a custom local port:

```bat
pipeline\17_local_api_server\run.bat --port 8877
```

Run tests:

```bat
py -m pytest tests\00_project_contract tests\01_find_input_workbook tests\02_read_xlsx_workbook tests\03_trim_workbook tests\04_garmin_activity_ingest tests\05_normalize_daily_records tests\06_normalize_activities tests\07_build_daily_features tests\08_compute_load_metrics tests\09_compute_readiness tests\10_compute_pws_components tests\11_compute_pws_weights tests\12_compute_pws_score tests\13_validate_llm_weight_influence tests\15_build_dashboard_payload tests\16_persist_local_snapshot tests\17_local_api_server
```

Run visualization:

```bat
visualization\17_local_api_server\run_visualization.bat
```

Install runtime dependencies from `requirements.txt` before serving with FastAPI and uvicorn if they are not already available.
