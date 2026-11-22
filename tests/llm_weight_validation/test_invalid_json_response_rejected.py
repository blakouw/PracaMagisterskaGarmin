from helpers import read_output

def test_invalid_json(module13, fake_root, invalid_json, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    assert module13.run(["--enable-llm"], injected_llm_client=invalid_json, root=fake_root) == 0
    out = read_output(fake_root)
    assert out["status"] == "llm_response_invalid"
    assert out["record"]["llm_assisted_status"] == "error_llm_no_assisted_score_delivered"
    assert out["record"]["pws_llm_assisted_computed"] is False
    assert out["record"]["llm_tool_execution"]["succeeded"] is False
