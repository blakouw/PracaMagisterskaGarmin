import json

from helpers import read_output

def allow_legacy_no_adjustment(fake_root):
    path = fake_root / "config" / "llm_weight_adjustment_prompt_v1.json"
    prompt = json.loads(path.read_text(encoding="utf-8"))
    prompt["required_response_schema"]["properties"]["decision"]["enum"] = ["no_adjustment", "propose_adjustment"]
    path.write_text(json.dumps(prompt, indent=2), encoding="utf-8")


def test_no_adjustment_records_same_score_as_assisted_variant(module13, fake_root, no_adjustment, monkeypatch):
    allow_legacy_no_adjustment(fake_root)
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    module13.run(["--enable-llm"], injected_llm_client=no_adjustment, root=fake_root)
    record = read_output(fake_root)["record"]
    assert record["pws_llm_assisted_computed"] is True
    assert record["pws_llm_assisted_delta_from_deterministic"] == 0.0
    assert record["llm_adjustment_applied"] is False
    assert record["llm_assisted_status"] == "no_adjustment_assisted_score_recorded"
