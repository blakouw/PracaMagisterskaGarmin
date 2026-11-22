import csv
from .helpers12 import full_fixture_records, run_module, setup_root


def test_csv_output(tmp_path):
    components, weights = full_fixture_records()
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
    with (root / "data/pipeline/12_compute_pws_score/pws_score.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["date"] == "2026-01-01"
    assert rows[0]["pws_deterministic"] == "91.63"
