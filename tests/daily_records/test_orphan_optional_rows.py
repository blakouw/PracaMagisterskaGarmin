from daily_helpers import output_dir, read_json, run_success_fixture

def test_orphan_optional_rows_reported(module05, case_root) -> None:
    run_success_fixture(case_root)
    assert module05.execute(root=case_root) == 0
    quality = read_json(output_dir(case_root) / "data_quality_report.json")
    assert quality["date_quality"]["orphan_optional_rows_count"] == 1
    assert quality["orphan_optional_rows"][0]["date"] == "2026-05-22"
