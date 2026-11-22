import csv
from .helpers10 import output, run_module, setup_root


def test_csv_output(tmp_path):
    root = setup_root(tmp_path)
    assert run_module(root) == 0
    with output(root, "pws_components.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert "pws_score" not in rows[0]
    assert "lq_score" in rows[0]
