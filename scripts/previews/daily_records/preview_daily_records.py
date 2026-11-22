from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data" / "pipeline" / "05_normalize_daily_records"
DAILY = BASE / "daily_records.json"
QUALITY = BASE / "data_quality_report.json"
SCHEMA = BASE / "daily_records_schema.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview normalized Garmin daily records.")
    parser.add_argument("--show-records", action="store_true", help="Show a small local sample of records. May contain private data.")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    if not DAILY.is_file() or not QUALITY.is_file() or not SCHEMA.is_file():
        print("Normalized daily record artifacts do not exist. Run pipeline/05_normalize_daily_records/run.bat first.")
        return 1
    daily = read_json(DAILY)
    quality = read_json(QUALITY)
    schema = read_json(SCHEMA)
    print("Normalized Daily Records")
    print("========================")
    print(f"status: {daily.get('status')}")
    print(f"records_count: {daily.get('records_count')}")
    print(f"date_range: {daily.get('date_range', {}).get('first_date')} .. {daily.get('date_range', {}).get('last_date')}")
    print(f"ready_for_next_module: {daily.get('ready_for_next_module')}")
    print("\nFields:")
    print(", ".join(daily.get("fields", [])))
    print("\nConsumed sheets:")
    for item in quality.get("consumed_sheets", []):
        print(f"- {item.get('sheet_name')}: {item.get('status')} ({item.get('rows_count')} rows)")
    print("\nIgnored sheets:")
    for item in quality.get("ignored_sheets", []):
        print(f"- {item.get('sheet_name')}: {item.get('reason')}")
    print("\nField coverage:")
    for field, cov in quality.get("field_coverage", {}).items():
        marker = " low" if cov.get("coverage_ratio", 0) < 0.5 else ""
        print(f"- {field}: {cov.get('available_count')}/{quality.get('records_count')} ({cov.get('coverage_ratio')}){marker}")
    print(f"\nfield_conflicts_count: {len(quality.get('field_conflicts', []))}")
    print(f"orphan_optional_rows_count: {len(quality.get('orphan_optional_rows', []))}")
    print(f"weight_grams_to_kilograms_count: {quality.get('unit_conversions_applied', {}).get('weight_grams_to_kilograms_count', 0)}")
    print("missing_values_policy: preserve_as_null")
    print("activities_and_derived_metrics: excluded")
    if args.show_records:
        print("\nRecord sample:")
        for record in daily.get("records", [])[: max(0, args.limit)]:
            print(json.dumps(record, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
