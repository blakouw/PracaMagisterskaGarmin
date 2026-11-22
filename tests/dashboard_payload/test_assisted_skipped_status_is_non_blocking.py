from dashboard_helpers import read_output, write_assisted
def test_skipped(module15, fake_root):
    write_assisted(fake_root, status="skipped_llm_disabled", computed=False)
    assert module15.build(fake_root)[0] == 0
    assert read_output(fake_root)["current_state"]["optional_assisted_pws"]["status"]=="not_available_llm_path_skipped"

