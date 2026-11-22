from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/pipeline/08_compute_load_metrics"
REQUIRED = [
    OUT / "load_metrics.json",
    OUT / "load_metrics_quality_report.json",
    OUT / "load_metrics_schema.json",
    OUT / "load_metrics_lineage.json",
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview normalized load metrics without printing private records by default.")
    parser.add_argument("--show-records", action="store_true")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--show-date")
    parser.add_argument("--show-chart-data", action="store_true")
    args = parser.parse_args()

    if not all(path.exists() for path in REQUIRED):
        print("Load metric artifacts do not exist. Run pipeline/08_compute_load_metrics/run.bat first.")
        return 1

    load_metrics = read_json(REQUIRED[0])
    quality = read_json(REQUIRED[1])
    schema = read_json(REQUIRED[2])
    lineage = read_json(REQUIRED[3])
    records = load_metrics.get("records", [])

    print("08_compute_load_metrics preview")
    print(f"Status: {load_metrics.get('status')}")
    print(f"Load source: {load_metrics.get('load_source_field')}")
    print("Limitation: active_kcal is a proxy load signal, not TRIMP, session-RPE or a medical model.")
    print(f"Records: {load_metrics.get('records_count')}")
    print(f"Date range: {load_metrics.get('date_range', {}).get('first_date')}..{load_metrics.get('date_range', {}).get('last_date')}")
    calendar = quality.get("calendar_axis_quality", {})
    print(f"Calendar gaps: {len(calendar.get('missing_calendar_dates', []))}")
    print(f"EWMA contiguous sequences: {len(calendar.get('contiguous_sequences', []))}")
    availability = quality.get("metric_availability", {})
    for field in ["acute_rolling_7d", "chronic_rolling_28d", "acwr_rolling", "acwr_ewma", "monotony_7d", "strain_7d"]:
        data = availability.get(field, {})
        print(f"{field}: available={data.get('available_count')} first={data.get('first_available_date')}")
    print(f"ACWR rolling zones: {quality.get('acwr_zone_counts', {}).get('rolling')}")
    print(f"ACWR EWMA zones: {quality.get('acwr_zone_counts', {}).get('ewma')}")
    parquet = quality.get("parquet_output", {})
    print(f"Outputs: JSON=true CSV=true Parquet={parquet.get('written')} warning={parquet.get('warning')}")
    print(f"Lineage groups: {[g.get('group_name') for g in lineage.get('metric_groups', [])]}")
    print(f"Schema fields: {len(schema.get('fields', []))}")
    print("Readiness and PWS were not computed.")
    print(f"Ready for 09_compute_readiness: {load_metrics.get('ready_for_next_module')}")

    selected = records
    if args.show_date:
        selected = [record for record in records if record.get("date") == args.show_date]
    if args.show_chart_data:
        chart_fields = [
            "date",
            "load_active_kcal",
            "acute_rolling_7d",
            "chronic_rolling_28d",
            "acwr_rolling",
            "acute_ewma_7d",
            "chronic_ewma_28d",
            "acwr_ewma",
        ]
        for record in selected[: max(0, args.limit)]:
            print(json.dumps({field: record.get(field) for field in chart_fields}, ensure_ascii=False))
    elif args.show_records or args.show_date:
        for record in selected[: max(0, args.limit)]:
            print(json.dumps(record, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
