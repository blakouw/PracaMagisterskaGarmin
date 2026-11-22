import csv
from helpers07 import setup_root, run_module
def test_csv_output(tmp_path):
    root = setup_root(tmp_path)
    assert run_module(root) == 0
    with (root / "data/pipeline/07_build_daily_features/daily_features.csv").open(encoding="utf-8", newline="") as h:
        rows = list(csv.DictReader(h))
    assert rows[0]["date"] == "2026-01-01"
    assert "activity_count" in rows[0]
