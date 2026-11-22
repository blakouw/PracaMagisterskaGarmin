from helpers import FakeLLM, read_output

def test_extra_fields(module13, fake_root, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    fake = FakeLLM(module13, {"decision": "no_adjustment", "reason_summary": "x", "proposed_weight_deltas": {"LQ": 0, "REC": 0, "CAP": 0, "VS": 0}, "extra": 1})
    assert module13.run(["--enable-llm"], injected_llm_client=fake, root=fake_root) == 0
    out = read_output(fake_root)
    assert out["status"] == "llm_response_invalid"
    assert out["record"]["llm_assisted_status"] == "error_llm_no_assisted_score_delivered"
    assert out["record"]["llm_tool_execution"]["error"] == "LLM_RESPONSE_SCHEMA_INVALID"
