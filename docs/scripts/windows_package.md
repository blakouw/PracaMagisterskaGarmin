# 19 Packaging Windows

Status: implemented.

This module builds a local portable Windows bundle for the already implemented dashboard application. It packages a production UI build and a minimal localhost runtime that serves both static UI assets and `/api/v1` read-only endpoints from one local process.

The packaged runtime is not a Vite development server. `pipeline\18_angular_dashboard_ui\build.bat` creates production assets first, then this module copies those assets into the release tree.

The package is local-only. It binds to `127.0.0.1:8765`, opens the dashboard in the browser, and reads the published current snapshot from a data directory next to the executable:

```text
data\published\dashboard_snapshots\current\
```

Private snapshot files are not copied into the package. The package contains only a placeholder telling the user where to place an already published current snapshot.

## Outputs

The module writes operational artifacts to:

```text
data\pipeline\19_packaging_windows\
```

The portable release is written to:

```text
release\windows\PersonalWellnessDashboard_1.0.0_portable\
release\windows\PersonalWellnessDashboard_1.0.0_portable.zip
```

The release directory contains:

- `PersonalWellnessDashboard.exe`
- `START_DASHBOARD.bat`
- `README.txt`
- `runtime\ui\` with production static UI assets
- `config\` with public runtime policies
- `data\published\dashboard_snapshots\current\PLACE_CURRENT_SNAPSHOT_HERE.txt`
- `manifests\windows_package_manifest.json`
- `manifests\windows_package_integrity.json`
- `manifests\windows_package_privacy_audit.json`

## Boundaries

This module does not create an installer, auto-updater, cloud deployment, LAN service, authentication layer, user profile, Garmin token pipeline, Garmin synchronization, analytical pipeline runner, LLM integration, coaching, medical diagnosis, injury prediction or training prescription.

The package must not contain private Garmin exports, FIT/TCX files, current snapshots, dashboard payloads, tokens, secrets, raw LLM responses or private runtime logs.

## Run

Build the portable package:

```bat
pipeline\19_packaging_windows\run.bat
```

Use an existing UI dist without rebuilding it:

```bat
pipeline\19_packaging_windows\run.bat --skip-ui-build
```

Build without the ZIP archive:

```bat
pipeline\19_packaging_windows\run.bat --no-zip
```

Run tests:

```bat
py -m pytest tests\19_packaging_windows -q
```

Run visualization:

```bat
visualization\19_packaging_windows\run_visualization.bat
```

Passing this packaging step does not approve public deployment or medical interpretation. It only creates a local portable runtime for already published dashboard snapshot data.
