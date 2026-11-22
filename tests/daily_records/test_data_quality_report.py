from daily_helpers import output_dir, read_json, run_success_fixture

def test_data_quality_report(module05, case_root) -> None:
    run_success_fixture(case_root)
    assert module05.execute(root=case_root) == 0
    quality = read_json(output_dir(case_root) / "data_quality_report.json")
    assert quality["records_count"] == 2
    assert quality["field_coverage"]["sleep_seconds"]["available_count"] == 1
    assert quality["field_coverage"]["sleep_seconds"]["coverage_ratio"] == 0.5
    assert quality["warnings"][0].startswith("Missing values")
