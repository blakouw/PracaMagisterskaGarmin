from helpers import read_output
def test_valid_adjustment(module13, fake_root, valid_adjustment, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY","x")
    module13.run(["--enable-llm","--date","2026-01-01"], injected_llm_client=valid_adjustment, root=fake_root)
    out=read_output(fake_root)
    assert out["status"] == "completed_assisted_score_computed"
    assert out["record"]["validated_llm_adjusted_weights"] == {"LQ":0.19,"REC":0.35,"CAP":0.16,"VS":0.3}
