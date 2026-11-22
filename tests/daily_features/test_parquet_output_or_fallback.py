from helpers07 import setup_root, run_module, output
def test_parquet_status_reported(tmp_path):
    root = setup_root(tmp_path)
    assert run_module(root) == 0
    pq = output(root, "daily_features_quality_report.json")["parquet_output"]
    assert pq["requested"] is True
    assert "written" in pq
