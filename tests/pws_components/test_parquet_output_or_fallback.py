from .helpers10 import output, read_json, run_module, setup_root


def test_parquet_or_fallback(tmp_path):
    root = setup_root(tmp_path)
    assert run_module(root) == 0
    parquet = read_json(output(root, "pws_components_quality_report.json"))["parquet_output"]
    assert parquet["requested"] is True
    if parquet["written"]:
        assert output(root, "pws_components.parquet").exists()
    else:
        assert parquet["warning"]
