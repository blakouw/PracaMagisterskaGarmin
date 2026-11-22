from __future__ import annotations

from pathlib import Path

from synthetic_input_factory import create_file, execute, make_case_root, manifest, selected_relative_path


def test_temporary_and_similar_nonmatching_files_do_not_affect_selection(tmp_path: Path) -> None:
    root = make_case_root(tmp_path, search_directories=["data/input"])
    create_file(root, "data/input/garmin_export_2026-05-01.xlsx")
    create_file(root, "data/input/~$garmin_export_2026-05-01.xlsx")
    create_file(root, "data/input/garmin_export_2026-05-01.xlsx.tmp")
    create_file(root, "data/input/.garmin_export_2026-05-01.xlsx")

    assert execute(root) == 0

    payload = manifest(root)
    assert payload["candidates_count"] == 1
    assert selected_relative_path(root) == "data/input/garmin_export_2026-05-01.xlsx"
    assert payload["warnings"] == []
