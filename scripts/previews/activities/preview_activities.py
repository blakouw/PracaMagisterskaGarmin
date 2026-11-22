from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data" / "pipeline" / "06_normalize_activities"
ACTIVITIES = BASE / "activities_normalized.json"
BY_DATE = BASE / "activities_by_date.json"
QUALITY = BASE / "activity_data_quality_report.json"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview normalized Garmin activities.")
    parser.add_argument("--show-activities", action="store_true")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--show-date")
    parser.add_argument("--show-activity-id")
    args = parser.parse_args()
    if not ACTIVITIES.is_file() or not BY_DATE.is_file() or not QUALITY.is_file():
        print("Normalized activity artifacts do not exist. Run pipeline/06_normalize_activities/run.bat first.")
        return 1
    activities = read_json(ACTIVITIES)
    by_date = read_json(BY_DATE)
    quality = read_json(QUALITY)
    print("Normalized Activities")
    print("=====================")
    print(f"status: {activities.get('status')}")
    print(f"activities_count: {activities.get('activities_count')}")
    dr = activities.get('date_range', {})
    print(f"date_range: {dr.get('first_date')} .. {dr.get('last_date')}")
    print(f"workbook_source: {quality.get('source_availability', {}).get('workbook_activities_csv_available')}")
    print(f"api_manifest: {quality.get('source_availability', {}).get('api_ingest_manifest_available')}")
    print(f"api_only_count: {quality.get('api_only_activities_count')}")
    print(f"field_conflicts_count: {len(quality.get('field_conflicts', []))}")
    print(f"excluded_invalid_records_count: {len(quality.get('excluded_invalid_records', []))}")
    counts = quality.get('source_record_counts', {})
    print(f"fit_files_available_count: {counts.get('fit_files_available_count', 0)}")
    print(f"tcx_files_available_count: {counts.get('tcx_files_available_count', 0)}")
    print("fit_tcx_parsed: false")
    print("derived_metrics_calculated: false")
    print(f"ready_for_next_module: {activities.get('ready_for_next_module')}")
    print("\nActivities per date:")
    for date, rows in by_date.get("activities_by_date", {}).items():
        print(f"- {date}: {len(rows)}")
    print("\nField coverage:")
    for field, cov in quality.get("field_coverage", {}).items():
        print(f"- {field}: {cov.get('available_count')}/{quality.get('normalized_activities_count')} ({cov.get('coverage_ratio')})")
    rows = activities.get("activities", [])
    if args.show_date:
        rows = [r for r in rows if r.get("date") == args.show_date]
        args.show_activities = True
    if args.show_activity_id:
        rows = [r for r in rows if r.get("activity_id") == args.show_activity_id]
        args.show_activities = True
    if args.show_activities:
        print("\nActivity sample:")
        for row in rows[: max(0, args.limit)]:
            print(json.dumps(row, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
