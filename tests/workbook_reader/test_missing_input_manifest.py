import json


def test_missing_input_manifest_fails_cleanly(case_root, module02) -> None:
    exit_code = module02.execute(case_root)
    artifact_dir = case_root / "data" / "pipeline" / "02_read_xlsx_workbook"
    errors = json.loads((artifact_dir / "errors.json").read_text(encoding="utf-8"))
    run_manifest = json.loads((artifact_dir / "run_manifest.json").read_text(encoding="utf-8"))
    structure = json.loads((artifact_dir / "workbook_structure.json").read_text(encoding="utf-8"))

    assert exit_code == 1
    assert errors["errors"][0]["code"] == "INPUT_MANIFEST_NOT_FOUND"
    assert run_manifest["execution_status"] == "failed"
    assert run_manifest["domain_status"] == "blocked_missing_input_manifest"
    assert structure["ready_for_next_module"] is False
