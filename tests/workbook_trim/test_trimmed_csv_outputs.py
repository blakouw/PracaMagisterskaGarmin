import csv

from trim_helpers import run_success_fixture


def test_trimmed_csv_keeps_policy_order_records_and_raw_values(case_root, module03) -> None:
    run_success_fixture(case_root)
    assert module03.execute(case_root) == 0
    csv_path = case_root / "data" / "pipeline" / "03_trim_workbook" / "trimmed_sheets" / "Daily_Summary.csv"
    rows = list(csv.reader(csv_path.open("r", encoding="utf-8", newline="")))
    header = rows[0]
    assert header[:3] == ["calendarDate", "activeKilocalories", "totalSteps"]
    assert "unknown" not in header
    assert rows[1][0] == "2026-01-01"
    assert rows[1][1] == "100"
    assert rows[2][0] == "2026-01-02"
    assert rows[2][1] == ""
    assert rows[2][2] == "2345"