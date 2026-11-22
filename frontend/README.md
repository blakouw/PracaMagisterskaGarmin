# 18 Local Dashboard UI

This module builds a local dashboard user interface consuming only the local dashboard API. It does not read pipeline or snapshot files directly and does not recompute analytical values. It also includes a local LLM chat panel that sends messages only to the approved localhost API chat endpoint.

Deterministic PWS is always the primary displayed score. An optional validated LLM-assisted PWS may be displayed only as a separately labelled comparison variant and must never replace the deterministic score.

Missing values remain unavailable and are displayed as missing data, never as numeric zero. Scores computed from partial eligible coverage must visibly disclose that limitation.

The frontend uses local same-origin API paths with a development proxy to the localhost API. It must not require wildcard CORS or expose private data outside the local machine.

This module does not implement authentication, user profiles, Garmin token management, pipeline execution, direct browser-to-LLM calls, medical diagnoses, injury predictions, coaching messages or training prescriptions.

## Purpose

`18_angular_dashboard_ui` is the local presentation layer after `17_local_api_server`. It renders a single dashboard screen from read-only API endpoints and stays inside the modular pipeline folder structure.

The module uses Vite, React and TypeScript because no previously implemented frontend stack exists in this repository. The existing module identifier and folder are preserved.

## Inputs

- `config/local_dashboard_ui_policy_v1.json`
- `config/dashboard_snapshot_api_policy_v1.json`
- `data/pipeline/17_local_api_server/api_contract_schema.json`
- `data/pipeline/17_local_api_server/api_quality_report.json`
- local API endpoints under `/api/v1`

## Runtime

The UI is local-only and read-only. In development, Vite serves the frontend on `127.0.0.1:5173` and proxies `/api` requests to `http://127.0.0.1:8765`.

Run the API and UI in separate terminals:

```bat
pipeline\17_local_api_server\run.bat
pipeline\18_angular_dashboard_ui\run.bat
```

Build and validate:

```bat
pipeline\18_angular_dashboard_ui\build.bat
```

## Dashboard Sections

- app status header and snapshot status
- primary deterministic PWS
- optional assisted PWS as a separate variant
- readiness
- PWS components
- deterministic weights
- load metrics
- time series
- PWS model comparison over time: deterministic, local LLM and external OpenAI
- daily signal charts for RHR, sleep, HRV, stress and activity HR when present in the API payload
- separate dynamically scaled PWS component weight charts for deterministic, local LLM and OpenAI variants
- clickable PWS component input-variable charts
- quality and coverage
- disclosures
- local LLM snapshot chat

## Boundaries

The UI does not start the API, run the pipeline, fetch Garmin data, call an LLM provider directly from the browser, edit weights, write settings, implement auth, implement profiles or manage Garmin tokens. The chat panel uses only POST /api/v1/dashboard/chat on localhost and does not modify snapshots. Public deployment is not approved in this module.

The API loads one snapshot at startup; restart the local API after publishing a new snapshot.

The signal and input-variable charts are presentation-only. They consume the `/api/v1/dashboard/time-series` payload and do not compute PWS, readiness, components or weights in the browser.

Each weight chart uses its own data-driven vertical domain and displays weights as percentages. Axis scaling changes presentation only and never changes source weight values.

The PWS model comparison panel also uses only API payload fields. It preserves missing provider values as unavailable, labels the external model, and never promotes either assisted series over deterministic PWS.

## Tests

Python contract tests:

```bat
py -m pytest tests\18_angular_dashboard_ui -q
```

Frontend tests:

```bat
cd pipeline\18_angular_dashboard_ui\app
npm test
```

Visualization:

```bat
visualization\18_angular_dashboard_ui\run_visualization.bat
```
