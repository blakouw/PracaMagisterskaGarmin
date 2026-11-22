from daily_helpers import copy_policy, load_policy, output_dir, read_json, write_policy, write_trim_artifacts

def test_required_field_mappings_are_blocking(module05, case_root) -> None:
    copy_policy(case_root)
    policy = load_policy(case_root)
    policy["primary_source_date_field"] = "missingDate"
    write_policy(case_root, policy)
    write_trim_artifacts(case_root, {"Daily_Summary": [{"calendarDate": "2026-01-01", "activeKilocalories": "1"}]})
    assert module05.execute(root=case_root) != 0
    assert read_json(output_dir(case_root) / "run_manifest.json")["domain_status"] == "blocked_missing_required_field_mapping"
