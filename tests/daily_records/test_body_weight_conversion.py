from daily_helpers import copy_policy, output_dir, read_json, write_trim_artifacts

def test_body_weight_conversion(module05, case_root) -> None:
    copy_policy(case_root)
    write_trim_artifacts(case_root, {
        "Daily_Summary": [
            {"calendarDate": "2026-01-01", "activeKilocalories": "1"},
            {"calendarDate": "2026-01-02", "activeKilocalories": "2"},
            {"calendarDate": "2026-01-03", "activeKilocalories": "3"},
        ],
        "Range_Body_Composition": [
            {"calendarDate": "2026-01-01", "weight": "78400"},
            {"calendarDate": "2026-01-02", "weight": "78.4"},
            {"calendarDate": "2026-01-03", "weight": "bad"},
        ],
    })
    assert module05.execute(root=case_root) == 0
    records = read_json(output_dir(case_root) / "daily_records.json")["records"]
    quality = read_json(output_dir(case_root) / "data_quality_report.json")
    assert records[0]["weight_kg"] == 78.4
    assert records[1]["weight_kg"] == 78.4
    assert records[2]["weight_kg"] is None
    assert quality["unit_conversions_applied"]["weight_grams_to_kilograms_count"] == 1
    assert quality["invalid_numeric_values"]
