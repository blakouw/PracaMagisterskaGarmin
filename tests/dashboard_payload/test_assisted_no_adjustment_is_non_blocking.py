from dashboard_helpers import read_output, write_assisted
def test_no_adjustment(module15, fake_root):
    write_assisted(fake_root, status="completed_no_adjustment_proposed", computed=False)
    module15.build(fake_root)
    assert read_output(fake_root)["current_state"]["optional_assisted_pws"]["status"]=="not_available_no_adjustment_proposed"

