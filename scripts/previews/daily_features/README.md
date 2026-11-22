# 07 Build Daily Features Visualization

This local preview reads module 07 artifacts and prints metadata, quality coverage and lineage. It does not run the production module and does not show full private records unless explicitly requested.

Run:

```bat
visualization\07_build_daily_features\run_visualization.bat
```

Optional local debug:

```bat
python visualization\07_build_daily_features\preview_daily_features.py --show-records --limit 5
python visualization\07_build_daily_features\preview_daily_features.py --show-date 2026-01-01
python visualization\07_build_daily_features\preview_daily_features.py --show-coverage
```
