from dashboard_helpers import read_output, write_assisted
def test_assisted_previous(module15, fake_root):
    write_assisted(fake_root, date="2026-01-02")
    module15.build(fake_root)
    assert read_output(fake_root)["current_state"]["optional_assisted_pws"]["status"]=="not_available_for_current_date"

