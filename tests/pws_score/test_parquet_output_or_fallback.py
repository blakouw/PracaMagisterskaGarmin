from .helpers12 import full_fixture_records, read_json, run_module, setup_root


def test_parquet_output_or_fallback(tmp_path):
    components, weights = full_fixture_records()
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
    parquet = read_json(root / "data/pipeline/12_compute_pws_score/pws_score_quality_report.json")["parquet_output"]
    assert parquet["written"] in {True, False}
    if not parquet["written"]:
        assert parquet["warning"] in {"PARQUET_DEPENDENCY_UNAVAILABLE", "PARQUET_WRITE_FAILED"}
