import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def test_prompt_template():
    p=json.loads((ROOT/"config/llm_weight_adjustment_prompt_v1.json").read_text(encoding="utf-8"))
    assert p["prompt_version"] == "llm_weight_adjustment_prompt_v1"
    assert p["required_response_schema"]["additionalProperties"] is False
    assert "medical diagnoses" in p["system_instruction"]
