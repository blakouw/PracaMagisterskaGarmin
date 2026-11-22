import csv
from .helpers09 import output, run_module, setup_root, base_record


def test_csv_output(tmp_path):
    root = setup_root(tmp_path, records=[base_record()])
    assert run_module(root) == 0
    with output(root, "readiness.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["readiness_score"] == "88.91"
    assert "pws_score" not in rows[0]
