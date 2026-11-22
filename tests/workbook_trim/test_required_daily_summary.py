import json

from trim_helpers import copy_policy, write_module02_artifacts, daily_summary_sheet


def test_existing_daily_summary_allows_trim(case_root, module03) -> None:
    copy_policy(case_root)
    write_module02_artifacts(case_root, [daily_summary_sheet(extra_headers=["totalSteps"])])
    assert module03.execute(case_root) == 0
    manifest = json.loads((case_root / "data" / "pipeline" / "03_trim_workbook" / "trimmed_sheets_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "trimmed"
    assert manifest["ready_for_next_module"] is True
    assert manifest["sheets"][0]["classification"] == "KEEP_REQUIRED"


def test_missing_daily_summary_blocks(case_root, module03) -> None:
    copy_policy(case_root)
    write_module02_artifacts(case_root, [{"sheet_name": "Daily_Sleep", "headers": ["calendarDate"], "rows": []}])
    exit_code = module03.execute(case_root)
    manifest = json.loads((case_root / "data" / "pipeline" / "03_trim_workbook" / "trimmed_sheets_manifest.json").read_text(encoding="utf-8"))
    errors = json.loads((case_root / "data" / "pipeline" / "03_trim_workbook" / "errors.json").read_text(encoding="utf-8"))
    assert exit_code == 1
    assert manifest["status"] == "blocked_missing_required_sheet"
    assert {sheet["sheet_name"] for sheet in manifest["missing_sheets"]} >= {"Daily_Summary"}
    assert errors["errors"][0]["code"] == "REQUIRED_SHEET_MISSING"