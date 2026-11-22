from dashboard_helpers import read_output
def test_no_assisted(module15, fake_root):
    assert module15.build(fake_root)[0] == 0
    assert read_output(fake_root)["current_state"]["optional_assisted_pws"]["status"]=="not_available_no_assisted_artifact"

