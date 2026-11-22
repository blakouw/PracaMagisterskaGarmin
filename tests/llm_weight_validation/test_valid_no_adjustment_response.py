import json

from helpers import read_output

def allow_legacy_no_adjustment(fake_root):
    path = fake_root / "config" / "llm_weight_adjustment_prompt_v1.json"
    prompt = json.loads(path.read_text(encoding="utf-8"))
    prompt["required_response_schema"]["properties"]["decision"]["enum"] = ["no_adjustment", "propose_adjustment"]
    path.write_text(json.dumps(prompt, indent=2), encoding="utf-8")


def test_valid_no_adjustment(module13, fake_root, no_adjustment, monkeypatch):
    allow_legacy_no_adjustment(fake_root)
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    assert module13.run(["--enable-llm"], injected_llm_client=no_adjustment, root=fake_root) == 0
    out = read_output(fake_root)
    record = out["record"]
    assert out["status"] == "completed_no_adjustment_proposed"
    assert record["pws_llm_assisted"] == record["pws_deterministic"]
    assert record["pws_llm_assisted_computed"] is True
    assert record["llm_tool_execution"] == {
        "tool_name": "persist_llm_assisted_pws_record",
        "attempted": True,
        "succeeded": True,
        "error": None,
    }
