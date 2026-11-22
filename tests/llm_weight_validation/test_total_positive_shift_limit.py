from helpers import FakeLLM, read_output
def test_positive_shift_limit(module13, fake_root, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY","x")
    fake=FakeLLM(module13, {"decision":"propose_adjustment","reason_summary":"x","proposed_weight_deltas":{"LQ":-0.06,"REC":0.06,"CAP":-0.06,"VS":0.06}})
    module13.run(["--enable-llm","--date","2026-01-01"], injected_llm_client=fake, root=fake_root)
    assert "Maximum total positive weight shift exceeded." in read_output(fake_root,"llm_validation_report.json")["violations"]
