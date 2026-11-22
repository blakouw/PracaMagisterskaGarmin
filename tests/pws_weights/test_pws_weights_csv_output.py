import csv
from .helpers11 import component_record, run_module, setup_root


def test_pws_weights_csv_output(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01")])
    assert run_module(root) == 0
    with (root / "data/pipeline/11_compute_pws_weights/pws_weights.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["date"] == "2026-01-01"
    assert "deterministic_effective_weight_lq" in rows[0]
