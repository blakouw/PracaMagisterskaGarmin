import json

from trim_helpers import copy_policy


def test_missing_module02_artifacts_blocks(case_root, module03) -> None:
    copy_policy(case_root)
    exit_code = module03.execute(case_root)
    artifact_dir = case_root / "data" / "pipeline" / "03_trim_workbook"
    errors = json.loads((artifact_dir / "errors.json").read_text(encoding="utf-8"))
    run_manifest = json.loads((artifact_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert exit_code == 1
    assert errors["errors"][0]["code"] == "WORKBOOK_STRUCTURE_NOT_FOUND"
    assert run_manifest["execution_status"] == "failed"


def test_missing_raw_sheet_artifact_blocks(case_root, module03):
    copy_policy(case_root)
    artifact_dir = case_root / "data" / "pipeline" / "02_read_xlsx_workbook"
    artifact_dir.mkdir(parents=True)
    (artifact_dir / "workbook_structure.json").write_text('{"status":"parsed","ready_for_next_module":true}', encoding="utf-8")
    (artifact_dir / "raw_sheets_manifest.json").write_text('{"ready_for_next_module":true,"sheets":[{"sheet_name":"Daily_Summary","artifact_path":"data/pipeline/02_read_xlsx_workbook/raw_sheets/missing.json"}]}', encoding="utf-8")
    exit_code = module03.execute(case_root)
    errors = json.loads((case_root / "data" / "pipeline" / "03_trim_workbook" / "errors.json").read_text(encoding="utf-8"))
    assert exit_code == 1
    assert errors["errors"][0]["code"] == "RAW_SHEET_ARTIFACT_NOT_FOUND"