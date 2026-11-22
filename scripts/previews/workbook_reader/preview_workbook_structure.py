from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STRUCTURE_PATH = ROOT / "data" / "pipeline" / "02_read_xlsx_workbook" / "workbook_structure.json"
RAW_MANIFEST_PATH = ROOT / "data" / "pipeline" / "02_read_xlsx_workbook" / "raw_sheets_manifest.json"


def section(title: str) -> None:
    print()
    print(title)
    print("=" * len(title))


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview module 02 workbook structure artifacts.")
    parser.add_argument("--show-sheet", dest="show_sheet", help="Optionally show up to N rows from one raw sheet.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum rows to show with --show-sheet, capped at 5.")
    args = parser.parse_args()

    if not STRUCTURE_PATH.is_file() or not RAW_MANIFEST_PATH.is_file():
        print("Workbook structure artifacts do not exist. Run pipeline/02_read_xlsx_workbook/run.bat first.")
        return 1

    structure = read_json(STRUCTURE_PATH)
    raw_manifest = read_json(RAW_MANIFEST_PATH)
    source = structure.get("source_workbook") or {}
    parser_info = structure.get("parser", {})

    section("Workbook Structure")
    print(f"Workbook: {source.get('filename')}")
    print(f"Status: {structure.get('status')}")
    print(f"Parser: {parser_info.get('type')}")
    print(f"Shared strings present: {parser_info.get('shared_strings_present')}")
    print(f"Sheets: {structure.get('sheets_count')}")
    print(f"Ready for module 03: {structure.get('ready_for_next_module')}")

    artifacts_by_name = {sheet["sheet_name"]: sheet for sheet in raw_manifest.get("sheets", [])}
    section("Sheets")
    if not structure.get("sheets"):
        print("No parsed sheets.")
    for sheet in structure.get("sheets", []):
        print(f"- {sheet['sheet_name']}")
        print(f"  rows: {sheet['row_count']}, columns: {sheet['column_count']}")
        print(f"  headers: {', '.join(sheet.get('headers', []))}")
        artifact = artifacts_by_name.get(sheet["sheet_name"], {})
        print(f"  artifact: {artifact.get('artifact_path')}")
        for warning in sheet.get("warnings", []):
            print(f"  warning: {warning}")

    section("Warnings")
    warnings = structure.get("warnings", [])
    if not warnings:
        print("None")
    else:
        for warning in warnings:
            print(f"- {warning}")

    if args.show_sheet:
        limit = max(0, min(args.limit, 5))
        artifact = artifacts_by_name.get(args.show_sheet)
        if artifact is None:
            print(f"Sheet not found: {args.show_sheet}")
            return 1
        raw_path = ROOT / artifact["artifact_path"]
        raw_sheet = read_json(raw_path)
        section(f"Rows From {args.show_sheet}")
        print("These rows may contain private Garmin data.")
        for row in raw_sheet.get("rows", [])[:limit]:
            print(json.dumps(row, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
