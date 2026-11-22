import json
from pathlib import Path
from .helpers08 import make_records, output, read_json, run_module, setup_root


def test_outputs_do_not_contain_future_scores(tmp_path):
    root = setup_root(tmp_path, records=make_records([100] * 8))
    assert run_module(root) == 0
    data = read_json(output(root))
    forbidden = {"rhr_delta", "ln_rmssd", "readiness", "LQ", "REC", "CAP", "VS", "pws_score", "pws_weights", "pws_priority"}
    text = json.dumps(data)
    for field in forbidden:
        assert f'"{field}"' not in text


def test_module09_contract_can_be_implemented_without_changing_module08_outputs():
    root = Path(__file__).resolve().parents[2]
    contract = json.loads((root / "pipeline/09_compute_readiness/contract.json").read_text(encoding="utf-8"))
    assert contract["module_id"] == "09_compute_readiness"
