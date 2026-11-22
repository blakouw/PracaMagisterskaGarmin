from helpers import read_output
def test_validation_report(module13, fake_root, valid_adjustment, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY","x")
    module13.run(["--enable-llm","--date","2026-01-01"], injected_llm_client=valid_adjustment, root=fake_root)
    assert read_output(fake_root,"llm_validation_report.json")["validation_status"] == "accepted"
