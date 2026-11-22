from dashboard_helpers import read_output
def test_execution(module15, fake_root):
    assert module15.build(fake_root)[0] == 0
    assert read_output(fake_root)["ready_for_next_module"] is True

