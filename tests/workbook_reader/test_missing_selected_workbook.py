import json

from xlsx_helpers import write_workbook_manifest


def test_missing_selected_workbook_blocks_module(case_root, module02) -> None:
    write_workbook_manifest(case_root, None, status="missing")

    exit_code = module02.execute(case_root)

    artifact_dir = case_root / "data" / "pipeline" / "02_read_xlsx_workbook"
    errors = json.loads((artifact_dir / "errors.json").read_text(encoding="utf-8"))
    run_manifest = json.loads((artifact_dir / "run_manifest.json").read_text(encoding="utf-8"))
    structure = json.loads((artifact_dir / "workbook_structure.json").read_text(encoding="utf-8"))

    assert exit_code == 1
    assert errors["errors"][0]["code"] == "INPUT_WORKBOOK_NOT_SELECTED"
    assert run_manifest["domain_status"] == "blocked_missing_input_workbook"
    assert structure["sheets_count"] == 0
    assert structure["ready_for_next_module"] is False
