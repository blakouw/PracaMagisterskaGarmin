from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "data" / "pipeline" / "03_trim_workbook"
SUMMARY_PATH = ARTIFACT_DIR / "trim_summary.json"
MANIFEST_PATH = ARTIFACT_DIR / "trimmed_sheets_manifest.json"
REPORT_PATH = ARTIFACT_DIR / "trim_report.md"


def section(title: str) -> None:
    print()
    print(title)
    print("=" * len(title))


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview module 03 trim artifacts.")
    parser.add_argument("--show-sheet", dest="show_sheet")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    if not SUMMARY_PATH.is_file() or not MANIFEST_PATH.is_file():
        print("Trim artifacts do not exist. Run pipeline/03_trim_workbook/run.bat first.")
        return 1

    summary = read_json(SUMMARY_PATH)
    manifest = read_json(MANIFEST_PATH)

    section("Trim Summary")
    print(f"Status: {summary.get('status')}")
    print(f"Policy: {summary.get('policy_version')}")
    print(f"Source sheets: {summary.get('source_sheets_count')}")
    print(f"Ready for normalization: {summary.get('ready_for_next_module')}")
    print(f"Full report: {REPORT_PATH.relative_to(ROOT).as_posix()}")

    section("KEEP_REQUIRED")
    for sheet in [s for s in manifest.get("sheets", []) if s["classification"] == "KEEP_REQUIRED"]:
        print(f"- {sheet['sheet_name']}: {', '.join(sheet['kept_columns'])} -> {sheet['artifact_path']}")

    section("KEEP_OPTIONAL")
    optional = [s for s in manifest.get("sheets", []) if s["classification"] == "KEEP_OPTIONAL"]
    if not optional:
        print("None")
    for sheet in optional:
        print(f"- {sheet['sheet_name']}: {', '.join(sheet['kept_columns'])} -> {sheet['artifact_path']}")

    section("DROP_NOT_USED")
    dropped = manifest.get("dropped_sheets", [])
    if not dropped:
        print("None")
    for sheet in dropped:
        print(f"- {sheet['sheet_name']}")

    section("MISSING")
    missing = manifest.get("missing_sheets", [])
    if not missing:
        print("None")
    for sheet in missing:
        print(f"- {sheet['sheet_name']} ({sheet['classification']})")

    section("Missing Columns")
    any_missing = False
    for sheet in manifest.get("sheets", []):
        if sheet.get("missing_required_columns") or sheet.get("missing_optional_columns"):
            any_missing = True
            print(f"- {sheet['sheet_name']}")
            print(f"  required: {', '.join(sheet.get('missing_required_columns', [])) or 'none'}")
            print(f"  optional: {', '.join(sheet.get('missing_optional_columns', [])) or 'none'}")
    if not any_missing:
        print("None")

    section("Warnings")
    if not manifest.get("warnings"):
        print("None")
    for warning in manifest.get("warnings", []):
        print(f"- {warning}")

    if args.show_sheet:
        sheet = next((s for s in manifest.get("sheets", []) if s["sheet_name"] == args.show_sheet), None)
        if sheet is None:
            print(f"Sheet not found: {args.show_sheet}")
            return 1
        path = ROOT / sheet["artifact_path"]
        limit = max(0, min(args.limit, 5))
        section(f"Rows From {args.show_sheet}")
        print("These rows may contain private Garmin data.")
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for index, row in enumerate(reader):
                if index >= limit:
                    break
                print(json.dumps(row, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())