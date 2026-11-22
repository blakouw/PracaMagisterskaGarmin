import json
from pathlib import Path
from .helpers10 import output, read_json, run_module, setup_root


def test_no_final_pws_or_weights_in_records(tmp_path):
    root = setup_root(tmp_path)
    assert run_module(root) == 0
    records = read_json(output(root))["records"]
    forbidden = {"pws_score", "pws_deterministic", "pws_llm_assisted", "pws_weights", "effective_pws_weights", "dynamic_weights", "priority_component", "priority_recommendation", "llm_adjustment", "coach_message"}
    for record in records:
        assert not (forbidden & set(record))
        assert record["pws_weights_computed"] is False
        assert record["final_pws_computed"] is False


def test_module10_does_not_compute_weights():
    root = Path(__file__).resolve().parents[2]
    contract = json.loads((root / "pipeline/10_compute_pws_components/contract.json").read_text(encoding="utf-8"))
    assert "calculate_pws_weights" in contract["prohibited_responsibilities"]
