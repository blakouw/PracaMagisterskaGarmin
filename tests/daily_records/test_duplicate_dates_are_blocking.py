from daily_helpers import copy_policy, output_dir, read_json, write_trim_artifacts

def test_duplicate_dates_are_blocking(module05, case_root) -> None:
    copy_policy(case_root)
    write_trim_artifacts(case_root, {"Daily_Summary": [{"calendarDate": "2026-01-01", "activeKilocalories": "1"}, {"calendarDate": "2026-01-01", "activeKilocalories": "2"}]})
    assert module05.execute(root=case_root) != 0
    assert read_json(output_dir(case_root) / "run_manifest.json")["domain_status"] == "blocked_duplicate_dates"
