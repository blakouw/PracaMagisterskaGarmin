from __future__ import annotations

from pathlib import Path

from synthetic_input_factory import artifact_json, create_file, execute, make_case_root, manifest, selected_relative_path


def test_single_valid_workbook_is_found_without_requiring_valid_xlsx(tmp_path: Path) -> None:
    root = make_case_root(tmp_path)
    workbook = create_file(root, "data/input/garmin_export_2026-05-01.xlsx")

    assert execute(root) == 0

    payload = manifest(root)
    assert payload["status"] == "found"
    assert payload["candidates_count"] == 1
    assert selected_relative_path(root) == "data/input/garmin_export_2026-05-01.xlsx"
    assert payload["selected_workbook"]["filename"] == workbook.name
    assert payload["selected_workbook"]["extension"] == ".xlsx"
    assert payload["selected_workbook"]["size_bytes"] == 0
    assert payload["selected_workbook"]["exists"] is True
    assert payload["ready_for_next_module"] is True
    assert payload["warnings"] == []

    run_manifest = artifact_json(root, "run_manifest.json")
    assert run_manifest["execution_status"] == "success"
    assert run_manifest["domain_status"] == "found"
