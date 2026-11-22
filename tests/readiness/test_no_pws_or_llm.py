import json
from pathlib import Path
from .helpers09 import output, read_json, run_module, setup_root, base_record


def test_records_do_not_contain_pws_or_llm_fields(tmp_path):
    root = setup_root(tmp_path, records=[base_record()])
    assert run_module(root) == 0
    record = read_json(output(root))["records"][0]
    forbidden = {"LQ", "REC", "CAP", "VS", "pws_deterministic", "pws_llm_assisted", "pws_weights", "pws_priority", "llm_adjustment", "coach_message", "training_recommendation"}
    assert not (forbidden & set(record))


def test_module10_contract_can_be_implemented_without_changing_module09_outputs():
    root = Path(__file__).resolve().parents[2]
    contract = json.loads((root / "pipeline/10_compute_pws_components/contract.json").read_text(encoding="utf-8"))
    assert contract["module_id"] == "10_compute_pws_components"
