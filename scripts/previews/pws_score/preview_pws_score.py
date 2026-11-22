from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "data/pipeline/12_compute_pws_score"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require_artifacts():
    paths = [
        ARTIFACT_DIR / "pws_score.json",
        ARTIFACT_DIR / "pws_score_quality_report.json",
        ARTIFACT_DIR / "pws_score_schema.json",
        ARTIFACT_DIR / "pws_score_lineage.json",
    ]
    if not all(path.is_file() for path in paths):
        print("Deterministic PWS artifacts do not exist. Run pipeline/12_compute_pws_score/run.bat first.")
        raise SystemExit(1)
    return [read_json(path) for path in paths]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--show-records", action="store_true")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--show-date")
    parser.add_argument("--show-contributions", action="store_true")
    parser.add_argument("--show-coverage", action="store_true")
    parser.add_argument("--show-chart-data", action="store_true")
    args = parser.parse_args()
    pws, quality, schema, lineage = require_artifacts()
    records = pws.get("records", [])
    print(f"status: {pws.get('status')}")
    print(f"score_name: {pws.get('score_name')}")
    print(f"score_range: {pws.get('score_range')}")
    print(f"formula: {pws.get('formula')}")
    print(f"records_count: {pws.get('records_count')}")
    print(f"date_range: {pws.get('date_range')}")
    print(f"score_availability: {quality.get('score_availability')}")
    print(f"coverage_tiers: {quality.get('coverage_tiers')}")
    print(f"label_counts: {quality.get('label_counts')}")
    print("weight_source: deterministic_effective_weights from module 11 only")
    print("weights_recomputed: false; weights_modified: false")
    print("missing_components_replaced_with_zero: false")
    print(f"llm_called: {quality.get('llm_path', {}).get('llm_called')}")
    print(f"pws_llm_assisted_computed: {quality.get('llm_path', {}).get('pws_llm_assisted_computed')}")
    print("PWS is not a medical diagnosis or training prescription.")
    print(f"ready_for_next_module: {pws.get('ready_for_next_module')}")
    selected = records
    if args.show_date:
        selected = [record for record in records if record.get("date") == args.show_date]
    if args.show_records:
        for record in selected[: max(0, args.limit)]:
            print(json.dumps(record, indent=2, ensure_ascii=False))
    if args.show_contributions:
        for record in selected[: max(0, args.limit)]:
            print(record.get("date"), record.get("pws_weighted_contributions"))
    if args.show_coverage:
        for record in selected[: max(0, args.limit)]:
            print(record.get("date"), record.get("pws_coverage_tier"), record.get("pws_coverage_ratio"))
    if args.show_chart_data:
        for record in selected[: max(0, args.limit)]:
            scores = record.get("pws_component_scores", {})
            print(record.get("date"), record.get("pws_deterministic"), record.get("pws_coverage_ratio"), scores.get("LQ"), scores.get("REC"), scores.get("CAP"), scores.get("VS"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
