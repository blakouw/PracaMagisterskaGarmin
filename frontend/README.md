# Local Dashboard UI

The dashboard renders the current published snapshot through the local API. It uses Angular 22, TypeScript, Angular CLI with an esbuild-based builder, and responsive Chart.js charts through ng2-charts.

Deterministic PWS is the primary displayed score. The local and OpenAI-assisted scores are separate comparisons. Missing values appear as unavailable, and partial component coverage is disclosed. Charts show the values returned by the API and their display units.

## Run locally

From the repository root, install the Python requirements and start the API:

```powershell
python -m pip install -r requirements.txt
python -m backend.api_server
```

In a second terminal, use a Node.js version supported by Angular 22, such as Node.js 24.15 or later in the 24.x line:

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`. Angular CLI proxies `/api/**` to `http://127.0.0.1:8765`. The browser uses relative `/api/v1` URLs. The API loads the published snapshot at startup. Restart it after publishing a new snapshot.

From the repository root on Windows, `scripts\api_server.bat` and `scripts\dashboard.bat` provide the same launch commands.

## Dashboard sections

- Current deterministic PWS, coverage, and the optional local assisted variant
- PWS components, deterministic weights, and load metrics
- PWS model comparisons with selectable dates and 7-, 30-, 90-day and full ranges
- Toggleable daily signals, separate weight charts for the three variants, and component input trends
- Data quality, missing components, and local snapshot chat

Changing the range requests the selected slice from the local time-series endpoint. The chat panel sends messages only to the local dashboard API.

## Build and test

Run from `frontend/`:

```powershell
npm run build
npm test
```

Angular CLI writes the production bundle to `frontend/dist/`. Serve it with access to the local API under the same origin. On Windows, `scripts\build_dashboard.bat` builds, tests, and runs the dashboard contract validator from the repository root. Run the Python tests for dashboard data from the repository root with `python -m pytest tests/dashboard_payload`.
