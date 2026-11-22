from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "data" / "pipeline" / "04_garmin_activity_ingest" / "activity_ingest_manifest.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview Garmin activity ingest manifest.")
    parser.add_argument("--show-activity-manifest", dest="activity_id", help="Show only the per-activity download_manifest.json.")
    args = parser.parse_args()

    if not MANIFEST_PATH.is_file():
        print("Activity ingest manifest does not exist. Run pipeline/04_garmin_activity_ingest/run.bat first.")
        return 1

    manifest = read_json(MANIFEST_PATH)
    print("Garmin Activity Ingest")
    print("======================")
    print(f"optional_module: {manifest.get('optional_module')}")
    print(f"status: {manifest.get('status')}")
    print(f"enabled: {manifest.get('enabled', 'unknown')}")
    print(f"api_called: {manifest.get('api_called')}")
    print(f"activity_id_sources: {', '.join(manifest.get('activity_id_sources', [])) or '(none)'}")
    print(f"requested_count: {manifest.get('activities_requested_count', len(manifest.get('requested_activity_ids', [])))}")
    print(f"downloaded_count: {manifest.get('activities_downloaded_count', 0)}")
    print(f"failed_count: {manifest.get('activities_failed_count', 0)}")
    print(f"ready_for_optional_activity_normalization: {manifest.get('ready_for_optional_activity_normalization')}")
    print(f"does_not_block_workbook_pipeline: {manifest.get('does_not_block_workbook_pipeline')}")

    warnings = manifest.get("warnings", [])
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"- {warning}")

    print("\nActivities:")
    activities = manifest.get("activities", [])
    if not activities:
        print("- none")
    for activity in activities:
        print(f"- {activity.get('activity_id')}: {activity.get('status')} -> {activity.get('manifest_path')}")

    if args.activity_id:
        selected = next((item for item in activities if str(item.get("activity_id")) == args.activity_id), None)
        if selected is None:
            print(f"\nNo per-activity manifest found for {args.activity_id}.")
            return 1
        activity_manifest = ROOT / str(selected.get("manifest_path"))
        if not activity_manifest.is_file():
            print(f"\nPer-activity manifest does not exist: {selected.get('manifest_path')}")
            return 1
        print("\nPer-Activity Download Manifest:")
        print(json.dumps(read_json(activity_manifest), indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
