# Module 04 Visualization

This local helper previews `data/pipeline/04_garmin_activity_ingest/activity_ingest_manifest.json` without displaying tokens or full Garmin activity payloads.

Run:

```bat
visualization\04_garmin_activity_ingest\run_visualization.bat
```

Optional local debug:

```bat
python visualization\04_garmin_activity_ingest\preview_activity_ingest.py --show-activity-manifest 123456789
```

The optional argument prints only that activity's `download_manifest.json`; it does not open FIT, TCX, details JSON or splits JSON.
