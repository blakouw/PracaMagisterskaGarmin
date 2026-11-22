from daily_helpers import output_dir, read_json, run_success_fixture

def test_primary_date_normalization(module05, case_root) -> None:
    run_success_fixture(case_root)
    assert module05.execute(root=case_root) == 0
    daily = read_json(output_dir(case_root) / "daily_records.json")
    assert [r["date"] for r in daily["records"]] == ["2026-05-20", "2026-05-21"]
    assert daily["records_count"] == 2
