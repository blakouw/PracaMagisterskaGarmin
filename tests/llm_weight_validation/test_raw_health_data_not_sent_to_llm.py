from helpers import read_output
def test_raw_health_data_not_sent(module13, fake_root):
    module13.run(["--dry-run"], root=fake_root)
    assert "resting_hr_bpm" not in str(read_output(fake_root,"llm_request_audit.json"))
    assert read_output(fake_root,"llm_request_audit.json")["forbidden_context_confirmation"]["tokens_or_credentials_sent"] is False
