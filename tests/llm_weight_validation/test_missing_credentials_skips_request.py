from helpers import read_output
def test_missing_credentials_skips_request(module13, fake_root, no_adjustment, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    module13.run(["--enable-llm"], injected_llm_client=no_adjustment, root=fake_root)
    assert read_output(fake_root)["status"] == "skipped_missing_credentials"
