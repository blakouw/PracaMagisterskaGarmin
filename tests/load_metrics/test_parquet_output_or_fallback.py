from .helpers08 import make_records, output, read_json, run_module, setup_root


def test_parquet_written_or_reported_fallback(tmp_path):
    root = setup_root(tmp_path, records=make_records([100] * 8))
    assert run_module(root) == 0
    report = read_json(output(root, "load_metrics_quality_report.json"))
    parquet = report["parquet_output"]
    assert parquet["requested"] is True
    if parquet["written"]:
        assert output(root, "load_metrics.parquet").exists()
    else:
        assert parquet["warning"]
