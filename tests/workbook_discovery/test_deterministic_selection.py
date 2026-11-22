from __future__ import annotations

from pathlib import Path

from synthetic_input_factory import create_file, execute, make_case_root, selected_relative_path


def test_repeated_execution_selects_same_single_workbook(tmp_path: Path) -> None:
    root = make_case_root(tmp_path, search_directories=["data/input"])
    create_file(root, "data/input/garmin_export_2026-05-01.xlsx")

    results = []
    for _ in range(3):
        assert execute(root) == 0
        results.append(selected_relative_path(root))

    assert results == ["data/input/garmin_export_2026-05-01.xlsx"] * 3


def test_selection_does_not_depend_on_filesystem_iteration_order(tmp_path: Path) -> None:
    expected = "data/input/garmin_export_2026-04-30.xlsx"
    results: list[str | None] = []

    for index, filenames in enumerate(
        [
            ["garmin_export_2026-05-02.xlsx", "garmin_export_2026-04-30.xlsx", "garmin_export_2026-05-01.xlsx"],
            ["garmin_export_2026-04-30.xlsx", "garmin_export_2026-05-01.xlsx", "garmin_export_2026-05-02.xlsx"],
        ]
    ):
        root = make_case_root(tmp_path / f"order_{index}", search_directories=["data/input"])
        for filename in filenames:
            create_file(root, f"data/input/{filename}")
        assert execute(root) == 0
        results.append(selected_relative_path(root))

    assert results == [expected, expected]
