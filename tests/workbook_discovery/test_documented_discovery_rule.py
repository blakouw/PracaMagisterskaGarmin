from __future__ import annotations

from pathlib import Path

from synthetic_input_factory import create_file, execute, make_case_root, manifest, selected_relative_path


def test_documented_candidate_pattern_is_garmin_export_xlsx(tmp_path: Path) -> None:
    root = make_case_root(tmp_path, search_directories=["data/input"])
    create_file(root, "data/input/other_export_2026-05-01.xlsx")
    create_file(root, "data/input/garmin_export_2026-05-01.csv")
    create_file(root, "data/input/garmin_export_2026-05-01.xlsx")

    assert execute(root) == 0

    payload = manifest(root)
    assert [candidate["filename"] for candidate in payload["candidates"]] == [
        "garmin_export_2026-05-01.xlsx"
    ]
    assert selected_relative_path(root) == "data/input/garmin_export_2026-05-01.xlsx"


def test_documented_multiple_match_rule_is_first_sorted_match(tmp_path: Path) -> None:
    root = make_case_root(tmp_path, search_directories=["data/input"])
    create_file(root, "data/input/garmin_export_2026-05-02.xlsx")
    create_file(root, "data/input/garmin_export_2026-05-01.xlsx")

    assert execute(root) == 0

    assert selected_relative_path(root) == "data/input/garmin_export_2026-05-01.xlsx"
    assert manifest(root)["search_configuration"]["selection_strategy"] == "first_path_sorted_ascending"
