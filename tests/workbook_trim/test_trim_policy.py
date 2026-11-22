import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_trim_policy_shape_and_required_content() -> None:
    policy = json.loads((ROOT / "config" / "garmin_trim_policy_v1.json").read_text(encoding="utf-8"))
    assert policy["policy_version"] == "garmin_trim_policy_v1"
    assert policy["source_type"] == "raw_sheet_artifacts_from_module_02"
    assert policy["selection_mode"] == "explicit_allowlist"
    assert policy["sheet_matching_strategy"] == "exact_name"
    assert policy["column_matching_strategy"] == "exact_name"
    assert policy["unknown_sheets_policy"] == "drop_and_report"
    assert policy["unknown_columns_policy"] == "drop_and_report"
    assert policy["preserve_raw_values"] is True
    assert policy["perform_domain_transformations"] is False
    by_name = {sheet["sheet_name"]: sheet for sheet in policy["sheets"]}
    assert by_name["Daily_Summary"]["requirement"] == "required"
    assert by_name["Daily_Summary"]["required_columns"] == ["calendarDate", "activeKilocalories"]
    for sheet_name in ["Daily_Sleep", "Daily_HRV", "Daily_RHR", "Daily_Stress", "Daily_Respiration", "Daily_SpO2", "Daily_Intensity_Minutes", "Range_Daily_Steps", "Activities", "Range_Body_Composition"]:
        assert by_name[sheet_name]["requirement"] == "optional"