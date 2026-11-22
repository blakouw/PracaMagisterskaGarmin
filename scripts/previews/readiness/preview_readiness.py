from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/pipeline/09_compute_readiness"
REQUIRED = [
    OUT / "readiness.json",
    OUT / "readiness_quality_report.json",
    OUT / "readiness_schema.json",
    OUT / "readiness_lineage.json",
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview readiness artifacts without printing private records by default.")
    parser.add_argument("--show-records", action="store_true")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--show-date")
    parser.add_argument("--show-components", action="store_true")
    parser.add_argument("--show-chart-data", action="store_true")
    args = parser.parse_args()

    if not all(path.exists() for path in REQUIRED):
        print("Readiness artifacts do not exist. Run pipeline/09_compute_readiness/run.bat first.")
        return 1

    readiness = read_json(REQUIRED[0])
    quality = read_json(REQUIRED[1])
    schema = read_json(REQUIRED[2])
    lineage = read_json(REQUIRED[3])
    records = readiness.get("records", [])
    print("09_compute_readiness preview")
    print(f"Status: {readiness.get('status')}")
    print(f"Score: {readiness.get('score_name')} range={readiness.get('score_range')}")
    print(f"Records: {readiness.get('records_count')}")
    print(f"Date range: {readiness.get('date_range', {}).get('first_date')}..{readiness.get('date_range', {}).get('last_date')}")
    print(f"Base weights: {readiness.get('base_component_weights')}")
    print(f"Minimum data requirements: {readiness.get('minimum_data_requirements')}")
    score = quality.get("score_availability", {})
    print(f"Computed readiness days: {score.get('computed_score_count')}")
    print(f"Insufficient data days: {score.get('insufficient_data_count')}")
    print(f"Labels: {quality.get('readiness_label_counts')}")
    print(f"Renormalized weight days: {len(quality.get('days_with_renormalized_weights', []))}")
    print(f"Clipped component days: {len(quality.get('days_with_clipped_component_values', []))}")
    print(f"Parquet: {quality.get('parquet_output')}")
    print("Readiness is deterministic, not PWS, not a medical diagnosis, and not a training prescription.")
    print(f"Ready for 10_compute_pws_components: {readiness.get('ready_for_next_module')}")
    if args.show_components:
        for name, details in quality.get("component_availability", {}).items():
            print(f"{name}: {details}")
        print(f"Lineage components: {[item.get('component') for item in lineage.get('component_lineage', [])]}")
        print(f"Schema fields: {len(schema.get('fields', []))}")
    selected = records
    if args.show_date:
        selected = [row for row in records if row.get("date") == args.show_date]
    if args.show_chart_data:
        fields = ["date", "readiness_score", "hrv_readiness_score", "stress_readiness_score", "rhr_readiness_score", "load_balance_readiness_score", "readiness_coverage_ratio"]
        for row in selected[: max(0, args.limit)]:
            print(json.dumps({field: row.get(field) for field in fields}, ensure_ascii=False))
    elif args.show_records or args.show_date:
        for row in selected[: max(0, args.limit)]:
            print(json.dumps(row, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
