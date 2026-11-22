from __future__ import annotations

from pathlib import Path

from synthetic_input_factory import artifact_json, create_file, execute, make_case_root, manifest


def test_empty_input_directories_report_controlled_missing_state(tmp_path: Path) -> None:
    root = make_case_root(tmp_path)

    assert execute(root) == 0

    payload = manifest(root)
    assert payload["status"] == "missing"
    assert payload["candidates"] == []
    assert payload["selected_workbook"] is None
    assert payload["ready_for_next_module"] is False
    assert "No Garmin workbook matching the configured filename pattern was found." in payload["warnings"]

    run_manifest = artifact_json(root, "run_manifest.json")
    errors = artifact_json(root, "errors.json")
    assert run_manifest["execution_status"] == "success"
    assert run_manifest["domain_status"] == "missing"
    assert errors == {"module_id": "01_find_input_workbook", "errors": []}


def test_nonmatching_files_do_not_create_false_workbook(tmp_path: Path) -> None:
    root = make_case_root(tmp_path)
    create_file(root, "notes.txt")
    create_file(root, "data/input/other_export.xlsx")
    create_file(root, "data/input/garmin_export_2026-05-01.csv")

    assert execute(root) == 0

    payload = manifest(root)
    assert payload["status"] == "missing"
    assert payload["candidates_count"] == 0
    assert payload["selected_workbook"] is None
