from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MODULE_ID = "15_build_dashboard_payload"
ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "data" / "pipeline" / MODULE_ID


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Preview dashboard payload artifacts.")
    parser.add_argument("--show-current-state", action="store_true")
    parser.add_argument("--show-series", action="store_true")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--show-date")
    parser.add_argument("--show-coverage", action="store_true")
    parser.add_argument("--show-disclosures", action="store_true")
    args = parser.parse_args(argv)
    required = ["dashboard_payload.json", "dashboard_payload_quality_report.json", "dashboard_payload_schema.json"]
    if any(not (ARTIFACT_DIR / name).is_file() for name in required):
        print(f"Dashboard payload artifacts do not exist. Run pipeline/15_build_dashboard_payload/run.bat first.")
        return 1
    payload = read_json(ARTIFACT_DIR / "dashboard_payload.json")
    quality = read_json(ARTIFACT_DIR / "dashboard_payload_quality_report.json")
    current = payload.get("current_state", {})
    primary = current.get("primary_pws", {})
    assisted = current.get("optional_assisted_pws", {})
    print(f"Module: {MODULE_ID}")
    print(f"Status: {payload.get('status')}")
    print(f"Latest date: {payload.get('metadata', {}).get('latest_date')}")
    print(f"Primary deterministic PWS: {primary.get('score')}")
    print(f"Primary computed: {primary.get('computed')}")
    print(f"Primary label: {primary.get('label_id')} / {primary.get('label')}")
    print(f"Coverage tier: {primary.get('coverage_tier')}")
    print(f"Optional assisted: {assisted.get('score') if assisted.get('available') else assisted.get('status')}")
    print(f"Readiness: {current.get('readiness', {}).get('score')}")
    print(f"LQ/REC/CAP/VS: {[current.get('pws_components', {}).get(c, {}).get('score') for c in ['LQ','REC','CAP','VS']]}")
    print(f"Deterministic weights: {current.get('pws_weights', {}).get('deterministic_effective_weights')}")
    print(f"Load metrics: {current.get('load_metrics')}")
    print(f"Records count: {payload.get('metadata', {}).get('records_count')}")
    print(f"Date range: {payload.get('metadata', {}).get('date_range')}")
    print(f"Primary PWS computed count: {quality.get('presentation_availability', {}).get('primary_pws_computed_count')}")
    print(f"Partial coverage count: {quality.get('coverage_tiers', {}).get('partial_eligible', 0)}")
    print(f"Unavailable PWS count: {quality.get('presentation_availability', {}).get('primary_pws_unavailable_count')}")
    print(f"Optional assisted source: {quality.get('optional_sources', {}).get('pws_llm_assisted')}")
    print("Deterministic PWS is primary: true")
    print("Analytical values recomputed: false")
    print("LLM called in this module: false")
    print("PWS is not a diagnosis or training prescription: true")
    print(f"Ready for next module: {payload.get('ready_for_next_module')}")
    if args.show_current_state:
        print(json.dumps(current, indent=2, ensure_ascii=False))
    if args.show_series:
        print(json.dumps(payload.get("time_series", [])[:args.limit], indent=2, ensure_ascii=False))
    if args.show_date:
        found = [row for row in payload.get("time_series", []) if row.get("date") == args.show_date]
        print(json.dumps(found, indent=2, ensure_ascii=False))
    if args.show_coverage:
        print(json.dumps(payload.get("quality_and_coverage", {}), indent=2, ensure_ascii=False))
    if args.show_disclosures:
        print(json.dumps(payload.get("disclosures", {}), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
