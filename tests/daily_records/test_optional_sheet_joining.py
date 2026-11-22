from daily_helpers import output_dir, read_json, run_success_fixture

def test_optional_sheet_joining(module05, case_root) -> None:
    run_success_fixture(case_root)
    assert module05.execute(root=case_root) == 0
    records = read_json(output_dir(case_root) / "daily_records.json")["records"]
    assert records[0]["sleep_seconds"] == 27000
    assert records[1]["sleep_seconds"] is None
