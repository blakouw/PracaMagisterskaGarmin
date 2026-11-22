from .helpers11 import component_record, read_json, run_module, setup_root


def test_parquet_output_or_fallback(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01")])
    assert run_module(root) == 0
    quality = read_json(root / "data/pipeline/11_compute_pws_weights/pws_weights_quality_report.json")
    parquet = quality["parquet_output"]
    assert parquet["written"] in {True, False}
    if not parquet["written"]:
        assert parquet["warning"] in {"PARQUET_DEPENDENCY_UNAVAILABLE", "PARQUET_WRITE_FAILED"}
