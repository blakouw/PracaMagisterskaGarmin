from daily_helpers import output_dir, read_json, run_success_fixture

def test_daily_records_outputs(module05, case_root) -> None:
    run_success_fixture(case_root)
    assert module05.execute(root=case_root) == 0
    base = output_dir(case_root)
    for name in ["daily_records.json", "daily_records.csv", "daily_records_schema.json", "data_quality_report.json", "run_manifest.json", "run_log.txt", "errors.json"]:
        assert (base / name).is_file()
    assert read_json(base / "daily_records.json")["ready_for_next_module"] is True
    assert read_json(base / "errors.json") == {"module_id": "05_normalize_daily_records", "errors": []}
