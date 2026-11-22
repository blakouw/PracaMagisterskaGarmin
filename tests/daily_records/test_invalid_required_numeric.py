from daily_helpers import copy_policy, output_dir, read_json, write_trim_artifacts

def test_invalid_required_numeric_value_blocks(module05, case_root) -> None:
    copy_policy(case_root)
    write_trim_artifacts(case_root, {"Daily_Summary": [{"calendarDate": "2026-01-01", "activeKilocalories": "bad"}]})
    assert module05.execute(root=case_root) != 0
    assert read_json(output_dir(case_root) / "run_manifest.json")["domain_status"] == "blocked_invalid_required_numeric_value"
