from daily_helpers import copy_policy, output_dir, read_json, write_policy, write_trim_artifacts

def test_invalid_policy_blocks(module05, case_root) -> None:
    copy_policy(case_root)
    policy = read_json(case_root / "config" / "garmin_daily_normalization_v1.json")
    policy["missing_values_policy"] = "fill_zero"
    write_policy(case_root, policy)
    write_trim_artifacts(case_root, {"Daily_Summary": [{"calendarDate": "2026-01-01", "activeKilocalories": "1"}]})
    assert module05.execute(root=case_root) != 0
    assert read_json(output_dir(case_root) / "run_manifest.json")["domain_status"] == "invalid_normalization_policy"
