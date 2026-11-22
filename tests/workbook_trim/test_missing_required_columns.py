import json

from trim_helpers import copy_policy, write_module02_artifacts


def run_with_headers(case_root, module03, headers):
    copy_policy(case_root)
    write_module02_artifacts(case_root, [{"sheet_name": "Daily_Summary", "headers": headers, "rows": [{"row_number": 2, "values": {header: "x" for header in headers}}]}])
    return module03.execute(case_root)


def test_missing_calendar_date_blocks(case_root, module03) -> None:
    assert run_with_headers(case_root, module03, ["activeKilocalories"]) == 1
    errors = json.loads((case_root / "data" / "pipeline" / "03_trim_workbook" / "errors.json").read_text(encoding="utf-8"))
    assert any(error["code"] == "REQUIRED_COLUMN_MISSING" and error["context"]["column_name"] == "calendarDate" for error in errors["errors"])


def test_missing_active_kilocalories_blocks(case_root, module03) -> None:
    assert run_with_headers(case_root, module03, ["calendarDate"]) == 1
    errors = json.loads((case_root / "data" / "pipeline" / "03_trim_workbook" / "errors.json").read_text(encoding="utf-8"))
    assert any(error["code"] == "REQUIRED_COLUMN_MISSING" and error["context"]["column_name"] == "activeKilocalories" for error in errors["errors"])