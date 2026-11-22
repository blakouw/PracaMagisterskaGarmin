from helpers import read_output
def test_dry_run_does_not_call_llm(module13, fake_root, no_adjustment, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY","x")
    module13.run(["--dry-run","--enable-llm"], injected_llm_client=no_adjustment, root=fake_root)
    assert no_adjustment.calls == 0
    assert read_output(fake_root)["status"] == "skipped_llm_disabled"
