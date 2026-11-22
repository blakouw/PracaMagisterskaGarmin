# Module 06 Visualization

Previews normalized activity artifacts without printing full private records by default.

Run:

```bat
visualization\06_normalize_activities\run_visualization.bat
```

Optional local debug:

```bat
python visualization\06_normalize_activities\preview_activities.py --show-activities --limit 5
python visualization\06_normalize_activities\preview_activities.py --show-date 2026-05-22
python visualization\06_normalize_activities\preview_activities.py --show-activity-id 123456789
```

Debug record output can contain private sport or location-related data. FIT and TCX file contents are not printed.
