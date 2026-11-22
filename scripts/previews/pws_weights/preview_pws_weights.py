from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "data/pipeline/11_compute_pws_weights"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require_artifacts() -> tuple[dict, dict, dict, dict, dict]:
    paths = [
        ARTIFACT_DIR / "pws_weights.json",
        ARTIFACT_DIR / "pws_weights_quality_report.json",
        ARTIFACT_DIR / "pws_weights_schema.json",
        ARTIFACT_DIR / "pws_weights_lineage.json",
        ARTIFACT_DIR / "pws_weight_guardrails.json",
    ]
    if not all(path.is_file() for path in paths):
        print("PWS weight artifacts do not exist. Run pipeline/11_compute_pws_weights/run.bat first.")
        raise SystemExit(1)
    return tuple(read_json(path) for path in paths)  # type: ignore[return-value]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--show-records", action="store_true")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--show-date")
    parser.add_argument("--show-base-weights", action="store_true")
    parser.add_argument("--show-effective-weights", action="store_true")
    parser.add_argument("--show-guardrails", action="store_true")
    parser.add_argument("--show-overlaps", action="store_true")
    args = parser.parse_args()
    weights, quality, schema, lineage, guardrails = require_artifacts()
    records = weights.get("records", [])
    print(f"status: {weights.get('status')}")
    print(f"records_count: {weights.get('records_count')}")
    print(f"date_range: {weights.get('date_range')}")
    print(f"base_component_weights: {weights.get('base_component_weights')}")
    print(f"base_weight_rationale: {lineage.get('base_weight_rationale')}")
    print(f"component_coverage: {quality.get('component_availability')}")
    print(f"weight_readiness: {quality.get('weight_readiness')}")
    print(f"deterministic_adjustment_usage: {quality.get('deterministic_adjustment_usage')}")
    print(f"overlap_controls: {quality.get('overlap_controls')}")
    print(f"llm_guardrails: max_delta={guardrails['future_llm_adjustment']['maximum_absolute_delta_per_component']} total_abs={guardrails['future_llm_adjustment']['maximum_total_absolute_delta']}")
    print(f"llm_called: {quality.get('future_llm_guardrails', {}).get('llm_called')}")
    print(f"final_pws_computed: {weights.get('final_pws_computed')}")
    print(f"ready_for_next_module: {weights.get('ready_for_next_module')}")
    if args.show_base_weights:
        print(json.dumps(weights.get("base_component_weights"), indent=2, ensure_ascii=False))
    if args.show_guardrails:
        print(json.dumps(guardrails, indent=2, ensure_ascii=False))
    if args.show_overlaps:
        print(json.dumps(lineage.get("deterministic_weighting_stages"), indent=2, ensure_ascii=False))
    selected = records
    if args.show_date:
        selected = [record for record in records if record.get("date") == args.show_date]
    if args.show_records:
        for record in selected[: max(0, args.limit)]:
            print(json.dumps(record, indent=2, ensure_ascii=False))
    if args.show_effective_weights:
        for record in selected[: max(0, args.limit)]:
            print(record.get("date"), record.get("deterministic_effective_weights"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
