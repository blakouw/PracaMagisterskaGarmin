from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/pipeline/10_compute_pws_components"
REQUIRED = [
    OUT / "pws_components.json",
    OUT / "pws_components_quality_report.json",
    OUT / "pws_components_schema.json",
    OUT / "pws_components_lineage.json",
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview PWS component artifacts without printing private records by default.")
    parser.add_argument("--show-records", action="store_true")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--show-date")
    parser.add_argument("--show-components", action="store_true")
    parser.add_argument("--show-coverage", action="store_true")
    parser.add_argument("--show-vs-signals", action="store_true")
    args = parser.parse_args()
    if not all(path.exists() for path in REQUIRED):
        print("PWS component artifacts do not exist. Run pipeline/10_compute_pws_components/run.bat first.")
        return 1
    payload = read_json(REQUIRED[0])
    quality = read_json(REQUIRED[1])
    schema = read_json(REQUIRED[2])
    lineage = read_json(REQUIRED[3])
    records = payload.get("records", [])
    print("10_compute_pws_components preview")
    print(f"Status: {payload.get('status')}")
    print(f"Components: {list(payload.get('component_definitions', {}).keys())}")
    print(f"Score range: {payload.get('component_score_range')}")
    print(f"Records: {payload.get('records_count')}")
    print(f"Date range: {payload.get('date_range', {}).get('first_date')}..{payload.get('date_range', {}).get('last_date')}")
    print(f"Component availability: {quality.get('component_availability')}")
    print(f"Daily coverage: {quality.get('daily_component_coverage')}")
    print(f"Known overlaps: {quality.get('known_component_overlaps')}")
    print(f"Parquet: {quality.get('parquet_output')}")
    print("Final PWS and weights were not computed. LLM was not used.")
    print(f"Ready for 11_compute_pws_weights: {payload.get('ready_for_next_module')}")
    if args.show_components:
        print(f"Lineage: {lineage.get('component_lineage')}")
        print(f"Schema fields: {schema.get('fields')}")
    if args.show_coverage:
        print(json.dumps(quality.get("component_availability"), ensure_ascii=False, sort_keys=True))
    selected = records
    if args.show_date:
        selected = [row for row in records if row.get("date") == args.show_date]
    if args.show_vs_signals:
        for row in selected[: max(0, args.limit)]:
            print(json.dumps({"date": row.get("date"), "vs_signal_details": row.get("vs_signal_details")}, ensure_ascii=False, sort_keys=True))
    elif args.show_records or args.show_date:
        for row in selected[: max(0, args.limit)]:
            print(json.dumps(row, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
