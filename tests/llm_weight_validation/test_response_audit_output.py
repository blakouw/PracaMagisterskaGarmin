from helpers import read_output
def test_response_audit(module13, fake_root):
    module13.run(["--dry-run"], root=fake_root)
    assert read_output(fake_root,"llm_response_audit.json")["llm_called"] is False
