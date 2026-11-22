from daily_helpers import copy_policy, output_dir, read_json, write_trim_artifacts

def test_primary_daily_summary_required(module05, case_root) -> None:
    copy_policy(case_root)
    write_trim_artifacts(case_root, {"Daily_Sleep": [{"calendarDate": "2026-01-01", "sleepDuration": "1"}]})
    assert module05.execute(root=case_root) != 0
    assert read_json(output_dir(case_root) / "run_manifest.json")["domain_status"] == "blocked_missing_primary_sheet"
