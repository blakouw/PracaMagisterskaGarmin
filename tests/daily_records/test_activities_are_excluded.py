from daily_helpers import copy_policy, output_dir, read_json, write_trim_artifacts

def test_activities_are_excluded(module05, case_root) -> None:
    copy_policy(case_root)
    write_trim_artifacts(case_root, {"Daily_Summary": [{"calendarDate": "2026-01-01", "activeKilocalories": "1"}], "Activities": [{"activityId": "1", "calendarDate": "2026-01-01"}]})
    assert module05.execute(root=case_root) == 0
    quality = read_json(output_dir(case_root) / "data_quality_report.json")
    assert any(item["sheet_name"] == "Activities" for item in quality["ignored_sheets"])
    fields = read_json(output_dir(case_root) / "daily_records.json")["fields"]
    assert "activityId" not in fields
