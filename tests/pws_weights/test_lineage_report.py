from .helpers11 import component_record, read_json, run_module, setup_root


def test_lineage_report(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01")])
    assert run_module(root) == 0
    lineage = read_json(root / "data/pipeline/11_compute_pws_weights/pws_weights_lineage.json")
    stages = [item["stage"] for item in lineage["deterministic_weighting_stages"]]
    assert "availability_renormalization" in stages
    assert lineage["future_llm_boundary"]["llm_called_in_this_module"] is False
