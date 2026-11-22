import json

from trim_helpers import run_success_fixture


def test_keep_drop_and_missing_column_classification(case_root, module03) -> None:
    run_success_fixture(case_root)
    assert module03.execute(case_root) == 0
    manifest = json.loads((case_root / "data" / "pipeline" / "03_trim_workbook" / "trimmed_sheets_manifest.json").read_text(encoding="utf-8"))
    daily = next(sheet for sheet in manifest["sheets"] if sheet["sheet_name"] == "Daily_Summary")
    assert daily["kept_required_columns"] == ["calendarDate", "activeKilocalories"]
    assert "totalSteps" in daily["kept_optional_columns"]
    assert "unknown" in daily["dropped_columns"]
    assert "restingHeartRate" in daily["missing_optional_columns"]
    classes = {(item["column_name"], item["classification"]) for item in daily["column_classifications"]}
    assert ("calendarDate", "KEEP_REQUIRED") in classes
    assert ("totalSteps", "KEEP_OPTIONAL") in classes
    assert ("unknown", "DROP_NOT_USED") in classes