from daily_helpers import copy_policy, output_dir, read_json, write_trim_artifacts

def test_field_source_priority_and_conflicts(module05, case_root) -> None:
    copy_policy(case_root)
    write_trim_artifacts(case_root, {
        "Daily_Summary": [{"calendarDate": "2026-01-01", "activeKilocalories": "1", "totalSteps": "100"}],
        "Range_Daily_Steps": [{"calendarDate": "2026-01-01", "totalSteps": "200"}],
    })
    assert module05.execute(root=case_root) == 0
    record = read_json(output_dir(case_root) / "daily_records.json")["records"][0]
    quality = read_json(output_dir(case_root) / "data_quality_report.json")
    assert record["steps"] == 200
    assert quality["field_conflicts"][0]["field"] == "steps"
