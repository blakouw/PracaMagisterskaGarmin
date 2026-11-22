from .helpers10 import output, read_json, run_module, setup_root


def test_lineage(tmp_path):
    root = setup_root(tmp_path)
    assert run_module(root) == 0
    lineage = read_json(output(root, "pws_components_lineage.json"))
    comps = {item["component"] for item in lineage["component_lineage"]}
    assert comps == {"LQ", "REC", "CAP", "VS"}
    assert lineage["forbidden_calculation_confirmation"]["llm_used"] is False
