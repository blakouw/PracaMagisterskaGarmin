import csv
from .helpers08 import make_records, output, run_module, setup_root


def test_csv_output_contains_flat_metrics(tmp_path):
    root = setup_root(tmp_path, records=make_records([100] * 8))
    assert run_module(root) == 0
    with output(root, "load_metrics.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 8
    assert rows[-1]["load_active_kcal"] == "100.0"
    assert "readiness" not in rows[-1]
