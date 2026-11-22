from __future__ import annotations

from pathlib import Path

from synthetic_input_factory import artifact_dir, artifact_json, artifact_text, create_file, execute, make_case_root


def test_module_01_execute_interface_generates_required_artifacts_in_synthetic_project(tmp_path: Path) -> None:
    root = make_case_root(tmp_path)
    create_file(root, "data/input/garmin_export_2026-05-01.xlsx")

    assert execute(root) == 0

    output_dir = artifact_dir(root)
    for filename in ["workbook_manifest.json", "run_manifest.json", "run_log.txt", "errors.json"]:
        assert (output_dir / filename).is_file(), filename

    workbook_manifest = artifact_json(root, "workbook_manifest.json")
    run_manifest = artifact_json(root, "run_manifest.json")
    errors = artifact_json(root, "errors.json")
    log_text = artifact_text(root, "run_log.txt")

    assert workbook_manifest["status"] == "found"
    assert workbook_manifest["selected_workbook"]["relative_path"] == "data/input/garmin_export_2026-05-01.xlsx"
    assert run_manifest["execution_status"] == "success"
    assert run_manifest["domain_status"] == workbook_manifest["status"]
    assert errors == {"module_id": "01_find_input_workbook", "errors": []}
    assert "xlsx_contents_read=false" in log_text
    assert "Workbook contents, sheets, cells and columns were not read." in log_text


def test_run_bat_exists_but_tests_do_not_need_real_project_artifacts() -> None:
    run_bat = Path(__file__).resolve().parents[2] / "pipeline" / "01_find_input_workbook" / "run.bat"
    assert run_bat.is_file()
    text = run_bat.read_text(encoding="utf-8")
    assert "pipeline\\01_find_input_workbook\\main.py" in text
