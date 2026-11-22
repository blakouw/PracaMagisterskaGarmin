import json

from trim_helpers import run_success_fixture


def test_keep_drop_and_missing_sheet_classification(case_root, module03) -> None:
    run_success_fixture(case_root)
    assert module03.execute(case_root) == 0
    manifest = json.loads((case_root / "data" / "pipeline" / "03_trim_workbook" / "trimmed_sheets_manifest.json").read_text(encoding="utf-8"))
    by_sheet = {sheet["sheet_name"]: sheet for sheet in manifest["sheets"]}
    assert by_sheet["Daily_Summary"]["classification"] == "KEEP_REQUIRED"
    assert by_sheet["Daily_Sleep"]["classification"] == "KEEP_OPTIONAL"
    assert {sheet["sheet_name"] for sheet in manifest["dropped_sheets"]} == {"Unused_Sheet"}
    missing = {sheet["sheet_name"]: sheet["classification"] for sheet in manifest["missing_sheets"]}
    assert missing["Daily_HRV"] == "MISSING_OPTIONAL"
    assert "Daily_Summary" not in missing