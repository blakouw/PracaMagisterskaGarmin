from __future__ import annotations

from pathlib import Path

from synthetic_input_factory import create_file, execute, make_case_root, manifest, selected_relative_path


def test_invalid_candidates_are_ignored_by_filename_pattern(tmp_path: Path) -> None:
    root = make_case_root(tmp_path, search_directories=["data/input"])
    create_file(root, "data/input/garmin_export_2026-05-01.xlsx")
    create_file(root, "data/input/garmin_export_2026-05-01.csv")
    create_file(root, "data/input/garmin_export_2026-05-01.json")
    create_file(root, "data/input/other_export_2026-05-01.xlsx")
    create_file(root, "data/input/notes.txt")

    assert execute(root) == 0

    payload = manifest(root)
    assert payload["candidates_count"] == 1
    assert [candidate["filename"] for candidate in payload["candidates"]] == [
        "garmin_export_2026-05-01.xlsx"
    ]
    assert selected_relative_path(root) == "data/input/garmin_export_2026-05-01.xlsx"
