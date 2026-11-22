from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "data" / "pipeline" / "07_build_daily_features"


def read(name: str) -> dict:
    return json.loads((DIR / name).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--show-records", action="store_true")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--show-date")
    parser.add_argument("--show-coverage", action="store_true")
    args = parser.parse_args()
    required = ["daily_features.json", "daily_features_quality_report.json", "daily_features_schema.json", "daily_features_lineage.json"]
    if not all((DIR / name).is_file() for name in required):
        print("Daily feature artifacts do not exist. Run pipeline/07_build_daily_features/run.bat first.")
        return 1
    features = read("daily_features.json")
    quality = read("daily_features_quality_report.json")
    schema = read("daily_features_schema.json")
    lineage = read("daily_features_lineage.json")
    print("Daily Features Preview")
    print(f"Status: {features.get('status')}")
    print(f"Records: {features.get('records_count')}")
    print(f"Date range: {features.get('date_range', {}).get('first_date')} .. {features.get('date_range', {}).get('last_date')}")
    print(f"Activity source used: {features.get('activity_source_used')}")
    print(f"Dates with activities: {quality.get('dates_with_activities_count')}")
    print(f"Dates without activities: {quality.get('dates_without_activities_count')}")
    print(f"Orphan activity dates: {len(quality.get('orphan_activity_dates', []))}")
    print(f"Parquet written: {quality.get('parquet_output', {}).get('written')}")
    print(f"Schema fields: {len(schema.get('fields', []))}")
    print("Field groups:")
    for group in lineage.get("field_groups", []):
        print(f"- {group.get('group_name')}: {len(group.get('fields', []))} fields from {group.get('origin_module')}")
    print("Derived metrics computed: false")
    print(f"Ready for 08_compute_load_metrics: {features.get('ready_for_next_module')}")
    if args.show_coverage:
        print("Coverage:")
        for field, cov in quality.get("feature_coverage", {}).items():
            total = cov.get("available_count", 0) + cov.get("missing_count", 0)
            print(f"- {field}: {cov.get('coverage_ratio')} ({cov.get('available_count')}/{total})")
    records = features.get("records", [])
    if args.show_date:
        print(json.dumps([r for r in records if r.get("date") == args.show_date][: args.limit], indent=2, ensure_ascii=False))
    elif args.show_records:
        print(json.dumps(records[: max(0, min(args.limit, 5))], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
