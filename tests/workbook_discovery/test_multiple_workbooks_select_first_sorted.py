from __future__ import annotations

from pathlib import Path

from synthetic_input_factory import create_file, execute, make_case_root, manifest, selected_relative_path


def test_multiple_workbooks_select_first_sorted_matching_file(tmp_path: Path) -> None:
    root = make_case_root(tmp_path, search_directories=["data/input"])
    create_file(root, "data/input/garmin_export_2026-05-02.xlsx", b"newer")
    create_file(root, "data/input/garmin_export_2026-05-01.xlsx", b"older")

    assert execute(root) == 0

    payload = manifest(root)
    paths = [candidate["relative_path"] for candidate in payload["candidates"]]
    assert paths == [
        "data/input/garmin_export_2026-05-01.xlsx",
        "data/input/garmin_export_2026-05-02.xlsx",
    ]
    assert selected_relative_path(root) == "data/input/garmin_export_2026-05-01.xlsx"
    assert payload["ready_for_next_module"] is True
    assert any("Multiple Garmin workbook candidates were found" in warning for warning in payload["warnings"])


def test_creation_order_does_not_change_first_sorted_selection(tmp_path: Path) -> None:
    expected = "data/input/garmin_export_A.xlsx"
    results: list[str | None] = []

    for index, creation_order in enumerate(
        [
            ["garmin_export_B.xlsx", "garmin_export_A.xlsx"],
            ["garmin_export_A.xlsx", "garmin_export_B.xlsx"],
        ]
    ):
        root = make_case_root(tmp_path / f"case_{index}", search_directories=["data/input"])
        for filename in creation_order:
            create_file(root, f"data/input/{filename}")

        assert execute(root) == 0
        results.append(selected_relative_path(root))

    assert results == [expected, expected]
