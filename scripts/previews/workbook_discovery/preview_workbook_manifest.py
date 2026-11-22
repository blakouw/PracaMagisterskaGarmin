from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "data" / "pipeline" / "01_find_input_workbook" / "workbook_manifest.json"


def section(title: str) -> None:
    print()
    print(title)
    print("=" * len(title))


def main() -> int:
    if not MANIFEST_PATH.is_file():
        print("Workbook manifest does not exist. Run pipeline/01_find_input_workbook/run.bat first.")
        return 1

    with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    config = manifest["search_configuration"]
    section("Workbook Search")
    print(f"Status: {manifest['status']}")
    print(f"Pattern: {config['filename_pattern']}")
    print(f"Search directories: {', '.join(config['search_directories'])}")
    print(f"Recursive: {config['recursive']}")
    print(f"Selection strategy: {config['selection_strategy']}")
    print(f"Candidates: {manifest['candidates_count']}")

    section("Candidates")
    if not manifest["candidates"]:
        print("No candidates.")
    else:
        print(f"{'Path':48} {'Size':>12} {'Modified':20} {'Exists'}")
        print("-" * 92)
        for candidate in manifest["candidates"]:
            print(
                f"{candidate['relative_path']:<48} "
                f"{candidate['size_bytes']:>12} "
                f"{candidate['modified_at']:<20} "
                f"{candidate['exists']}"
            )

    section("Selected Workbook")
    selected = manifest["selected_workbook"]
    if selected is None:
        print("None")
    else:
        print(f"Path: {selected['relative_path']}")
        print(f"Filename: {selected['filename']}")
        print(f"Extension: {selected['extension']}")
        print(f"Size bytes: {selected['size_bytes']}")
        print(f"Modified at: {selected['modified_at']}")

    section("Warnings")
    if not manifest["warnings"]:
        print("None")
    else:
        for warning in manifest["warnings"]:
            print(f"- {warning}")

    section("Next Module")
    print(f"Ready for 02_read_xlsx_workbook: {manifest['ready_for_next_module']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
