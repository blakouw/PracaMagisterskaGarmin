from helpers import FakeLLM, read_output
def test_overlap(module13, fake_root, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY","x")
    fake=FakeLLM(module13, {"decision":"propose_adjustment","reason_summary":"x","proposed_weight_deltas":{"LQ":-0.01,"REC":0.01,"CAP":0.0,"VS":0.0}})
    module13.run(["--enable-llm","--date","2026-01-01"], injected_llm_client=fake, root=fake_root)
    assert "Overlap controls were violated." in read_output(fake_root,"llm_validation_report.json")["violations"]
