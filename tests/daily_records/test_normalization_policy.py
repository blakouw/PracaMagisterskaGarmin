from daily_helpers import ROOT, read_json

def test_normalization_policy_shape() -> None:
    p = read_json(ROOT / "config" / "garmin_daily_normalization_v1.json")
    assert p["policy_version"] == "garmin_daily_normalization_v1"
    assert p["primary_sheet"] == "Daily_Summary"
    assert p["missing_values_policy"] == "preserve_as_null"
    assert p["duplicate_date_policy"] == "fail_for_consumed_daily_sheets"
    assert p["activities_sheet_policy"] == "exclude_from_this_module"
    assert "field_source_priority" in p
    assert "date" in p["output_fields"] and "active_kcal" in p["output_fields"]
