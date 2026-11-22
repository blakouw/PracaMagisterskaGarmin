from helpers import read_output
def test_weights_preserved(module13, fake_root, valid_adjustment, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY","x")
    module13.run(["--enable-llm","--date","2026-01-01"], injected_llm_client=valid_adjustment, root=fake_root)
    assert read_output(fake_root)["record"]["deterministic_effective_weights"] == {"LQ":0.2,"REC":0.35,"CAP":0.15,"VS":0.3}
