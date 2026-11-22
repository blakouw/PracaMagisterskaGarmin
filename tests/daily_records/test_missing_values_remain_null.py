import csv
from daily_helpers import output_dir, read_json, run_success_fixture

def test_missing_values_remain_null_and_empty_csv(module05, case_root) -> None:
    run_success_fixture(case_root)
    assert module05.execute(root=case_root) == 0
    records = read_json(output_dir(case_root) / "daily_records.json")["records"]
    assert records[1]["active_kcal"] is None
    assert records[1]["steps"] is None
    with (output_dir(case_root) / "daily_records.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[1]["active_kcal"] == ""
    assert rows[1]["steps"] == ""
