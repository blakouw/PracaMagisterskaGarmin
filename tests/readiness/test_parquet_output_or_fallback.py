from .helpers09 import output, read_json, run_module, setup_root, base_record


def test_parquet_written_or_fallback_reported(tmp_path):
    root = setup_root(tmp_path, records=[base_record()])
    assert run_module(root) == 0
    parquet = read_json(output(root, "readiness_quality_report.json"))["parquet_output"]
    assert parquet["requested"] is True
    if parquet["written"]:
        assert output(root, "readiness.parquet").exists()
    else:
        assert parquet["warning"]
